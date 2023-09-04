import json
import requests

from .constants import BASE_HEADERS, KickHelperException
from .kick_message import KickMessage


def get_streamer_info(bot) -> dict:
    """
    Retrieve dictionary containing all info related to the streamer.

    :param bot: main KickBot
    :return: dict containing all streamer info
    """
    url = f"https://kick.com/api/v2/channels/{bot.streamer_slug}"
    response = bot.client.scraper.get(url, cookies=bot.client.cookies, headers=BASE_HEADERS)
    status = response.status_code
    match status:
        case 403 | 429:
            raise KickHelperException(f"Error retrieving streamer info. Blocked By cloudflare. ({status})")
        case 404:
            raise KickHelperException(f"Streamer info for '{bot.streamer_name}' not found. (404 error) ")
    try:
        return response.json()
    except json.JSONDecodeError:
        raise KickHelperException(f"Error parsing streamer info json from response. Response: {response.text}")


def get_current_viewers(bot) -> int:
    """
    Retrieve current amount of viewers in the stream.

    :return: Viewer count as an integer
    """
    id = bot.streamer_info.get('id')
    url = f"https://api.kick.com/private/v0/channels/{id}/viewer-count"
    response = bot.client.scraper.get(url, cookies=bot.client.cookies, headers=BASE_HEADERS)
    if response.status_code != 200:
        raise KickHelperException(f"Error retrieving current viewer count. Response: {response.text}")
    data = response.json()
    try:
        return int(data.get('data').get('viewer_count'))
    except ValueError:
        raise KickHelperException(f"Error parsing viewer count. Response: {response.text}")


def get_chatroom_settings(bot) -> dict:
    url = f"https://kick.com/api/internal/v1/channels/{bot.streamer_slug}/chatroom/settings"
    response = bot.client.scraper.get(url, cookies=bot.client.cookies, headers=BASE_HEADERS)
    if response.status_code != 200:
        raise KickHelperException(f"Error retrieving chatroom settings. Response: {response.text}")
    return response.json().get('data').get('settings')


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


def send_reply_in_chat(bot, message: KickMessage, reply_message: str) -> requests.Response:
    """
    Reply to a users message.

    :param bot: KickBot main bot
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


def get_ws_uri() -> str:
    """
    This could probably be a constant somewhere else, but this makes it easy to get and easy to change.
    Also, they seem to always use the same ws, but in the case it needs to be dynamically found,
    having this function will make it easier.

    :return: kicks websocket url
    """
    return 'wss://ws-us2.pusher.com/app/eb1d5f283081a78b932c?protocol=7&client=js&version=7.6.0&flash=false'
