import requests

from kickbot import KickBot, KickMessage
from datetime import datetime, timedelta


async def time_following(bot: KickBot, message: KickMessage):
    """ Reply with the amount of time the user has been following for """
    sender_username = message.sender.username
    viewer_info = bot.moderator.get_viewer_info(sender_username)
    following_since = viewer_info.get('following_since')
    if following_since is not None:
        reply = f"You've been following since: {following_since}"
    else:
        reply = "Your not currently following this channel."
    await bot.reply_text(message, reply)


async def tell_a_joke(bot: KickBot, message: KickMessage):
    """ Reply with a random joke """
    url = "https://v2.jokeapi.dev/joke/Any?type=single"
    joke = requests.get(url).json().get('joke')
    await bot.reply_text(message, joke)


async def current_time(bot: KickBot, message: KickMessage):
    """ Reply with the current UTC time """
    time = datetime.utcnow().strftime("%I:%M %p")
    reply = f"Current UTC time: {time}"
    await bot.reply_text(message, reply)


async def ban_if_says_gay(bot: KickBot, message: KickMessage):
    """ Ban user for 20 minutes if they say 'your gay' """
    sender_username = message.sender.username
    ban_time = 20
    bot.moderator.timeout_user(sender_username, ban_time)


async def send_links_in_chat(bot: KickBot):
    """ Timed event to send social links every 30 mins """
    links = "Youtube: https://youtube.com\n\nTwitch: https://twitch.tv"
    await bot.send_text(links)


async def github_link(bot: KickBot, message: KickMessage):
    reply = "Github: 'https://github.com/lukemvc'"
    await bot.reply_text(message, reply)


if __name__ == '__main__':
    USERBOT_EMAIL = "user@example.com"
    USERBOT_PASS = "PasswordHere"
    STREAMER = "streamer_username"

    bot = KickBot(USERBOT_EMAIL, USERBOT_PASS)
    bot.set_streamer(STREAMER)

    bot.add_command_handler('!following', time_following)
    bot.add_command_handler('!joke', tell_a_joke)
    bot.add_command_handler('!time', current_time)
    bot.add_command_handler('!github', github_link)

    bot.add_message_handler('your gay', ban_if_says_gay)

    bot.add_timed_event(timedelta(minutes=30), send_links_in_chat)

    bot.poll()
