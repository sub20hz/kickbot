import json

from .kick_client import KickClient


HELPER_HEADERS = {
    "Accept": "application/json, text/plain, */*",
    "Accept-Encoding": "gzip, deflate, br",
    "Accept-Language": "en-US,en;q=0.9",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36",
}


class KickHelperException(Exception):
    ...


class KickHelper:
    @staticmethod
    def get_streamer_info(client: KickClient, streamer_name: str) -> dict:
        url = f"https://kick.com/api/v1/channels/{streamer_name}"
        response = client.scraper.get(url, cookies=client.cookies, headers=HELPER_HEADERS)
        if response.status_code == 403 | response.status_code == 429:
            raise KickHelperException("Error retrieving streamer info. Blocked By cloudflare.")
        try:
            return response.json()
        except json.JSONDecodeError:
            raise KickHelperException("Error parsing streamer info json from response.")

    @staticmethod
    def send_message_in_chat(bot, client: KickClient, message: str) -> dict:
        url = "https://kick.com/api/v1/chat-messages"
        HELPER_HEADERS['X-Xsrf-Token'] = client.xsrf
        HELPER_HEADERS['Authorization'] = "Bearer " + client.auth_token
        payload = {"message": message, "chatroom_id": bot.chatroom_id}
        return client.scraper.post(url, json=payload, cookies=client.cookies, headers=HELPER_HEADERS)
