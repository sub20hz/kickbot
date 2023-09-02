import asyncio
import json
import websockets

from datetime import datetime, timedelta

from .kick_client import KickClient
from .kick_helper import KickHelper


class SocketException(Exception):
    ...


class KickBotException(Exception):
    ...


class KickBot:
    """
    Main class for interacting with the Bot API.
    """
    def __init__(self, username: str, password: str) -> None:
        self._last_response: datetime | None = None
        self.client: KickClient = KickClient(username, password)
        self.ws_uri = self._get_ws_url()
        self.ws_auth_token: str | None = None
        self.userfeed_auth_token: str | None = None
        self.chat_auth_token: str | None = None
        self.socket_id: str | None = None
        self.streamer_name: str | None = None
        self.streamer_info: dict | None = None
        self.chatroom_info: dict | None = None
        self.chatroom_id: int | None = None

    async def poll(self) -> None:
        """
        Main function to poll the streamers chat and respond to messages/commands.
        """
        if self.streamer_name is None:
            raise KickBotException("Must set streamer name before polling.")

        async with websockets.connect(self.ws_uri) as self.sock:
            connection_response = await self._recv()
            await self._handle_first_connect(connection_response)
            await self._join_chatroom(self.chatroom_id)
            message_response = KickHelper.send_message_in_chat(self, "World")
            breakpoint()
            while True:
                try:
                    response = await self._recv()
                    print("Received:", response)
                    if response.get('event') == 'App\\Events\\ChatMessageEvent':
                        print("Handle chat message here.")

                    self._last_response = datetime.utcnow()

                except asyncio.exceptions.CancelledError:
                    break

        print(f"Disconnected from websocket {self.socket_id}")

    def set_streamer(self, streamer_name: str) -> None:
        """
        Set the streamer for the bot to monitor.

        :param streamer_name: Username of the streamer
        """
        if self.streamer_name is not None:
            raise KickBotException("Streamer already set. Only able to set one streamer at a time.")
        self.streamer_name = streamer_name
        self.streamer_info = KickHelper.get_streamer_info(self.client, streamer_name)
        try:
            self.chatroom_info = self.streamer_info.get('chatroom')
            self.chatroom_id = self.chatroom_info.get('id')
        except ValueError:
            raise KickBotException("Error retrieving streamer chatroom id.")

    async def _join_chatroom(self, chatroom_id: int) -> None:
        """
         Join the chatroom websocket.

         :param chatroom_id: ID of the chatroom, mainly the streamer to monitor
         """
        join_v2_command = {'event': 'pusher:subscribe', 'data': {'auth': '', 'channel': f"chatrooms.{chatroom_id}.v2"}}
        await self._send(join_v2_command)
        join_v2_response = await self._recv()
        print(f"Joined chatroom {chatroom_id} | Response: {join_v2_response} ")

    async def _handle_first_connect(self, connection_response: dict) -> None:
        """
        Handle the initial response received from the websocket.

        :param connection_response: Initial response when connecting to the socket
        """
        if connection_response.get('event') != 'pusher:connection_established':
            raise Exception('Error establishing connection to socket.')
        self.socket_id = json.loads(connection_response.get('data')).get('socket_id')
        print(f"Successfully Connected to socket... Socket ID: {self.socket_id}")
        await self._handle_first_socket_auth()

    async def _handle_first_socket_auth(self) -> None:
        """
        Handle the initial authentication in the websocket, after authenticating via http
        self.client.get_socket_auth_token uses the client.auth_token received from http login as Authorization header
        """
        # can also use private-App.User.{self.client.user_id} for channel_name (I think),
        # haven't really looked into the difference, but this is working for now.
        # HMAC SHA256 hex digest of 58469.447649:private-userfeed.18698546
        #                            socket_id        userfeed channel
        self.userfeed_auth_token = self.client.get_socket_auth_token(socket_id=self.socket_id,
                                                                     channel_name='private-userfeed.'
                                                                                  f'{self.client.user_id}')
        auth_command = {"event": "pusher:subscribe",
                        "data": {"auth": self.userfeed_auth_token,
                                 'channel': f'private-userfeed.{self.client.user_id}'}
                        }
        await self._send(auth_command)
        auth_response = await self._recv()
        if auth_response.get('event') != 'pusher_internal:subscription_succeeded':
            raise SocketException(f"Error authenticating on socket. {auth_response}")
        print(f"Socket Auth Response: {auth_response}")

    async def _send(self, command: dict) -> None:
        """
        Convert command to json and send over socket.

        :param command: dictionary to convert to json command
        """
        await self.sock.send(json.dumps(command))

    async def _recv(self) -> dict:
        """
        Receive socket inbound command and jsonify it

        :return: dict / json inbound socket command
        """
        return json.loads(await self.sock.recv())

    @staticmethod
    def _get_ws_url() -> str:
        """
        This could be a constant somewhere else, but this makes it ease and easy to change.
        Also, they seem to always use the same wss, but in the case it needs to be dynamically found,
        having this function will make it easier.

        :return: kicks websocket url
        """
        return 'wss://ws-us2.pusher.com/app/eb1d5f283081a78b932c?protocol=7&client=js&version=7.6.0&flash=false'
