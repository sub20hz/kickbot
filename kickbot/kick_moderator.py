import logging

from .kick_helper import (
    ban_user,
    get_viewer_info,
)

logger = logging.getLogger(__name__)


class Moderator:
    def __init__(self, bot) -> None:
        self.bot = bot

    def get_viewer_info(self, username) -> dict | None:
        """
        Returns Dictionary of user info containing things like 'following_since', 'subscribed_for', etc.

        :param username: User to retrieve info for
        :return: Dictionary of user info, will return None and log error if error fetching info
        """
        data = get_viewer_info(self.bot, username)
        return data

    def timeout_user(self, username: str, minutes: int) -> None:
        """
        Ban the user for a set amount of time.

        :param username: Username to ban
        :param minutes: Amount of time in minutes to ban user for
        """
        if ban_user(self.bot, username, minutes=minutes):
            logger.info(f"Banned user: {username} for {minutes} minutes.")

    def permaban(self, username) -> None:
        """
        Permanently ban a user

        :param username: Username to ban
        """
        if ban_user(self.bot, username, is_permanent=True):
            logger.info(f"Permanently banned user: {username}")
