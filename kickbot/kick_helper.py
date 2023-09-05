import logging
import requests

from .constants import BASE_HEADERS, KickHelperException
from .kick_message import KickMessage

logger = logging.getLogger(__name__)


def get_streamer_info(bot) -> None:
    """
    Retrieve dictionary containing all info related to the streamer and set bot attributes accordingly.
    """
    url = f"https://kick.com/api/v2/channels/{bot.streamer_slug}"
    response = bot.client.scraper.get(url, cookies=bot.client.cookies, headers=BASE_HEADERS)
    status = response.status_code
    match status:
        case 403 | 429:
            raise KickHelperException(f"Error retrieving streamer info. Blocked By cloudflare. ({status})")
        case 404:
            raise KickHelperException(f"Streamer info for '{bot.streamer_name}' not found. (404 error) ")
    data = response.json()
    bot.streamer_info = data
    bot.chatroom_info = data.get('chatroom')
    bot.chatroom_id = bot.chatroom_info.get('id')


def get_chatroom_settings(bot) -> None:
    """
    Retrieve chatroom settings for the streamer and set bot.chatroom_settings
    """
    url = f"https://kick.com/api/internal/v1/channels/{bot.streamer_slug}/chatroom/settings"
    response = bot.client.scraper.get(url, cookies=bot.client.cookies, headers=BASE_HEADERS)
    if response.status_code != 200:
        raise KickHelperException(f"Error retrieving chatroom settings. Response Status: {response.status_code}")
    data = response.json()
    bot.chatroom_settings = data.get('data').get('settings')


def get_bot_settings(bot) -> None:
    """
    Retrieve the bot settings for the stream. Checks if bot has mod / admin status. Sets attributes accordingly.
    """
    url = f"https://kick.com/api/v2/channels/{bot.streamer_slug}/me"
    headers = BASE_HEADERS.copy()
    headers['Authorization'] = "Bearer " + bot.client.auth_token
    headers['X-Xsrf-Token'] = bot.client.xsrf
    response = bot.client.scraper.get(url, cookies=bot.client.cookies, headers=headers)
    if response.status_code != 200:
        raise KickHelperException(f"Error retrieving bot settings. Response Status: {response.status_code}")
    data = response.json()
    bot.bot_settings = data
    bot.is_mod = data.get('is_moderator')
    bot.is_super_admin = data.get('is_super_admin')


def get_current_viewers(bot) -> int:
    """
    Retrieve current amount of viewers in the stream.

    :return: Viewer count as an integer
    """
    id = bot.streamer_info.get('id')
    url = f"https://api.kick.com/private/v0/channels/{id}/viewer-count"
    response = bot.client.scraper.get(url, cookies=bot.client.cookies, headers=BASE_HEADERS)
    if response.status_code != 200:
        logger.error(f"Error retrieving current viewer count. Response Status: {response.status_code}")
    data = response.json()
    try:
        return int(data.get('data').get('viewer_count'))
    except ValueError:
        logger.error(f"Error parsing viewer count. Response Status: {response.status_code}")


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

    :param bot: main KickBot
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


def ban_user(bot, username: str, minutes: int = 0, is_permanent: bool = False) -> bool:
    """
    Bans a user from chat. User by Moderator.timeout_user, and Moderator.permaban

    :param bot: Main KickBot
    :param username: Username to ban
    :param minutes: Minutes to ban user for
    :param is_permanent: Is a permanent ban. Defaults to False.
    """
    url = f"https://kick.com/api/v2/channels/{bot.streamer_slug}/bans"
    headers = BASE_HEADERS.copy()
    headers['path'] = f"/api/v2/channels/{bot.streamer_slug}/bans"
    headers['Authorization'] = "Bearer " + bot.client.auth_token
    headers['X-Xsrf-Token'] = bot.client.xsrf
    if is_permanent:
        payload = {
            "banned_username": username,
            "permanent": is_permanent
        }
    else:
        payload = {
            "banned_username": username,
            "duration": minutes,
            "permanent": is_permanent
        }
    response = bot.client.scraper.post(url, json=payload, cookies=bot.client.cookies, headers=headers)
    if response.status_code != 200:
        logger.error(f"An error occurred when setting timeout for {username} | "
                     f"Response Status: {response.status_code}")
        return False
    return True


def get_viewer_info(bot, username: str) -> dict | None:
    """
    For the Moderator to retrieve info on a user

    :param bot: Main KickBot
    :param username: Username to retrieve user info for

    :return: Dictionary containing viewer info, or None, indicating failure
    """
    slug = username.replace('_', '-')
    url = f"https://kick.com/api/v2/channels/lukemvc/users/{slug}"
    headers = BASE_HEADERS.copy()
    headers['Authorization'] = bot.client.auth_token
    headers['X-Xsrf-Token'] = bot.client.xsrf
    response = bot.client.scraper.get(url, cookies=bot.client.cookies, headers=headers)
    if response.status_code != 200:
        logger.error(f"Error retrieving viewer info for {username} | Status code: {response.status_code}")
        return None
    return response.json()


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
