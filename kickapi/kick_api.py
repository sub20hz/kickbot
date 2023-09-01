import asyncio
import json
import websockets

from client_auth import KickClient


class KickApi:
    def __init__(self, username: str, password: str) -> None:
        self.client: KickClient = KickClient(username, password)
        self.ws_uri = self._get_ws_url()
        self.socket_id: str | None = None

    async def poll(self) -> None:
        async with websockets.connect(self.ws_uri) as self.sock:
            connection_response = await self._recv()
            print("Connection Response:", connection_response)
            if connection_response.get('event') != 'pusher:connection_established':
                raise Exception('Error establishing connection to socket.')

            self.socket_id = json.loads(connection_response.get('data')).get('socket_id')
            print(f"Successfully Connected to socket... Socket ID: {self.socket_id}")

            ws_auth_token = self.client.get_socket_auth_token(socket_id=self.socket_id)
            auth_command = {"event": "pusher:subscribe",
                            "data": {"auth": ws_auth_token,
                                     'channel': f'private-userfeed.{self.client.user_id}'}
                            }
            await self._send(auth_command)
            
            ping_command = {"event": "pusher:ping", "data": {}}
            while True:
                try:
                    response = await self._recv()
                    print("Received:", response)
                    if response.get('event') in ['pusher:pong', 'pusher_internal:subscription_succeeded']:
                        print(True)
                        await self._send(ping_command)

                except asyncio.exceptions.CancelledError:
                    print("Disconnected.")
                    break

    async def _send(self, command: dict) -> None:
        await self.sock.send(json.dumps(command))

    async def _recv(self) -> dict[str, str | dict]:
        return json.loads(await self.sock.recv())

    @staticmethod
    def _get_ws_url() -> str:
        return 'wss://ws-us2.pusher.com/app/eb1d5f283081a78b932c?protocol=7&client=js&version=7.6.0&flash=false'
