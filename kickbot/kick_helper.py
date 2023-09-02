import json
import requests

from .constants import BASE_HEADERS
from .kick_client import KickClient


class KickHelperException(Exception):
    ...


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
        payload = {"message": message, "chatroom_id": bot.chatroom_id}
        return bot.client.scraper.post(url, json=payload, cookies=bot.client.cookies, headers=headers)
