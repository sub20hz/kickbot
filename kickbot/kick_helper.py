import json
import requests

from .constants import BASE_HEADERS, KickHelperException
from .kick_client import KickClient
from .kick_message import KickMessage


class KickHelper:
    @staticmethod
    def get_streamer_info(client: KickClient, streamer_name: str) -> dict:
        """
        Retrieve dictionary containing all info related to the streamer.

        :param client: KickClient object from KickBot for the scraper and cookies
        :param streamer_name: name of the streamer to retrieve info on
        :return: dict containing all streamer info
        """
        url = f"https://kick.com/api/v1/channels/{streamer_name}"
        response = client.scraper.get(url, cookies=client.cookies, headers=BASE_HEADERS)
        status = response.status_code
        match status:
            case 403 | 420:
                raise KickHelperException(f"Error retrieving streamer info. Blocked By cloudflare. ({status})")
            case 404:
                raise KickHelperException(f"Streamer info for '{streamer_name}' not found. (404 error) ")
        try:
            return response.json()
        except json.JSONDecodeError:
            raise KickHelperException(f"Error parsing streamer info json from response. Response: {response.text}")

    @staticmethod
    def send_message_in_chat(bot, message: str) -> requests.Response:
        """
        Send a message in a chatroom. Uses v1 API, was having csrf issues using v2 API (code 419).

        :param bot: KickBot object containing streamer, and bot info
        :param message: Message to send in the chatroom
        :return: Response from sending the message post request
        """
        url = "https://kick.com/api/v1/chat-messages"
        headers = BASE_HEADERS.copy()
        headers['X-Xsrf-Token'] = bot.client.xsrf
        headers['Authorization'] = "Bearer " + bot.client.auth_token
        payload = {"message": message,
                   "chatroom_id": bot.chatroom_id}
        return bot.client.scraper.post(url, json=payload, cookies=bot.client.cookies, headers=headers)

    @staticmethod
    def send_reply_in_chat(bot, message: KickMessage, reply_message: str) -> requests.Response:
        """
        Reply to a users message.

        :param bot: KickBot main bot (wasn't able to import class for type hint, would cause circular import)
        :param message: Original message to reply
        :param reply_message:  Reply message to be sent to the original message
        :return: Response from sending the message post request
        """
        url = f"https://kick.com/api/v2/messages/send/{bot.chatroom_id}"
        headers = BASE_HEADERS.copy()
        headers['X-Xsrf-Token'] = bot.client.xsrf
        headers['Authorization'] = "Bearer " + bot.client.auth_token
        payload = {
            "content": reply_message,
            "type": "reply",
            "metadata": {
                "original_message": {
                    "id": message.id,
                    "content": message.content
                },
                "original_sender": {
                    "id": message.sender.user_id,
                    "username": message.sender.username
                }
            }
        }
        return bot.client.scraper.post(url, json=payload, cookies=bot.client.cookies, headers=headers)

    @staticmethod
    def message_from_data(message: dict) -> KickMessage:
        """
        Return a KickMessage object from the raw message data, containing message and sender attributes.

        :param message: Inbound message from websocket
        :return: KickMessage object with message and sender attributes
        """
        data = message.get('data')
        if data is None:
            raise KickHelperException(f"Error parsing message data from response {message}")
        return KickMessage(data)

    @staticmethod
    def get_ws_uri() -> str:
        """
        This could probably be a constant somewhere else, but this makes it easy and easy to change.
        Also, they seem to always use the same wss, but in the case it needs to be dynamically found,
        having this function will make it easier.

        :return: kicks websocket url
        """
        return 'wss://ws-us2.pusher.com/app/eb1d5f283081a78b932c?protocol=7&client=js&version=7.6.0&flash=false'
