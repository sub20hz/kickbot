import asyncio
import json
import websockets

from typing import Callable

from .constants import KickBotException
from .kick_client import KickClient
from .kick_helper import KickHelper
from .kick_message import KickMessage


class KickBot:
    """
    Main class for interacting with the Bot API.
    """
    def __init__(self, username: str, password: str) -> None:
        self.client: KickClient = KickClient(username, password)
        self._ws_uri = KickHelper.get_ws_uri()
        self._socket_id: str | None = None
        self.streamer_name: str | None = None
        self.streamer_info: dict | None = None
        self.chatroom_info: dict | None = None
        self.chatroom_id: int | None = None
        self.handled_commands: dict[str, Callable] = {}
        self.handled_messages: dict[str, Callable] = {}

    def poll(self):
        """
        Main function to activate the bot polling.
        """
        try:
            asyncio.run(self._poll())
        except KeyboardInterrupt:
            print("Bot stopped.")
            return

    def add_message_handler(self, message: str, message_function: Callable) -> None:
        """
        Add a message to be handled, and the asynchronous function to handle that message.

        Command handler will call the function if the first word matches
        Message handler will call the function if the entire message content matches

        :param message: Message to be handled i.e: 'you are gay'
        :param message_function: Async function to handle the message
        """
        if self.streamer_name is None:
            raise KickBotException("Must set streamer name to monitor first.")
        message = message.casefold()
        if self.handled_messages.get('message') is not None:
            raise KickBotException(f"Message: {message} already set in handled messages")
        self.handled_messages[message] = message_function

    def add_command_handler(self, command: str, command_function: Callable) -> None:
        """
        Add a command to be handled, and the asynchronous function to handle that command.

        Command handler will call the function if the first word matches
        Message handler will call the function if the entire message content matches

        Inside the command handler function, you can access arguments of the command as a list.
        i.e: message.args = ['!hello', 'world', 'what's', 'up']
        """
        if self.streamer_name is None:
            raise KickBotException("Must set streamer name to monitor first.")
        command = command.casefold()
        if self.handled_commands.get('message') is not None:
            raise KickBotException(f"Command: {command} already set in handled commands")
        self.handled_commands[command] = command_function

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
            raise KickBotException("Error retrieving streamer chatroom id. Are you sure that username is correct?")

    async def send_text(self, message: str) -> None:
        """
        Used inside a command/message handler function, to send text in the chat.
        reply_text below is used to reply to a specific users message.

        :param message: Message to be sent in the chat
        """
        if not type(message) == str or message.strip() == "":
            raise KickBotException("Invalid message. Must be a non empty string.")
        print(f"Sending message: {message}")
        r = KickHelper.send_message_in_chat(self, message)
        if r.status_code != 200:
            raise KickBotException(f"An error occurred while sending message {message}")

    async def reply_text(self, original_message: KickMessage, reply_message: str) -> None:
        """
        Used inside a command/message handler function to reply to the original message.

        :param original_message: The original KickMessage argument in the handler function
        :param reply_message: string to reply to the original message
        """
        if not type(reply_message) == str or reply_message.strip() == "":
            raise KickBotException("Invalid reply message. Must be a non empty string.")
        print(f"Sending reply: {reply_message}")
        r = KickHelper.send_reply_in_chat(self, original_message, reply_message)
        if r.status_code != 200:
            raise KickBotException(f"An error occurred while sending reply {reply_message}")

    async def _poll(self) -> None:
        """
        Main internal function to poll the streamers chat and respond to messages/commands.
        """
        if self.streamer_name is None:
            raise KickBotException("Must set streamer name before polling.")
        async with websockets.connect(self._ws_uri) as self.sock:
            connection_response = await self._recv()
            await self._handle_first_connect(connection_response)
            await self._join_chatroom(self.chatroom_id)
            while True:
                try:
                    response = await self._recv()
                    if response.get('event') == 'App\\Events\\ChatMessageEvent':
                        await self._handle_chat_message(response)
                except asyncio.exceptions.CancelledError:
                    break
        print(f"Disconnected from websocket {self._socket_id}")

    async def _handle_chat_message(self, inbound_message: dict) -> None:
        """
        Handles incoming messages, checks if the message.content is in dict of handled commands

        :param inbound_message: Raw inbound message from socket
        """
        message: KickMessage = KickHelper.message_from_data(inbound_message)
        content = message.content.casefold()
        command = message.args[0].casefold()
        print(f"New Message from {message.sender.username} | MESSAGE: {content}")

        if content in self.handled_messages:
            message_func = self.handled_messages[content]
            await message_func(self, message)

        elif command in self.handled_commands:
            command_func = self.handled_commands[command]
            await command_func(self, message)

    async def _join_chatroom(self, chatroom_id: int) -> None:
        """
         Join the chatroom websocket.

         :param chatroom_id: ID of the chatroom, mainly the streamer to monitor
         """
        join_command = {'event': 'pusher:subscribe', 'data': {'auth': '', 'channel': f"chatrooms.{chatroom_id}.v2"}}
        await self._send(join_command)
        join_response = await self._recv()
        if join_response.get('event') != "pusher_internal:subscription_succeeded":
            raise KickBotException(f"Error when attempting to join chatroom {chatroom_id}. Response: {join_response}")
        print(f"Bot Joined chatroom {chatroom_id}")

    async def _handle_first_connect(self, connection_response: dict) -> None:
        """
        Handle the initial response received from the websocket.

        :param connection_response: Initial response when connecting to the socket
        """
        if connection_response.get('event') != 'pusher:connection_established':
            raise Exception('Error establishing connection to socket.')
        self._socket_id = json.loads(connection_response.get('data')).get('socket_id')
        print(f"Successfully Connected to socket... Socket ID: {self._socket_id}")

    async def _send(self, command: dict) -> None:
        """
        Json dumps command and sends over socket.

        :param command: dictionary to convert to json command
        """
        await self.sock.send(json.dumps(command))

    async def _recv(self) -> dict:
        """
        Json loads command received from socket.

        :return: dict / json inbound socket command
        """
        return json.loads(await self.sock.recv())


