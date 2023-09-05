# kickbot

### Unofficial python package to create bots and interact with the kick.com api

---
## Table of Contents

- [About](#about)
- [Installation](#installation)
- [Features](#features)
- [Example](#example)
- [Command / Message handling](#command-and-message-handling)
- [Sending Messages / Reply's](#sending-messages-and-replys)
- [Streamer / Chat information](#streamer-and-chat-information)
- [Chat Moderation](#chat-moderation)
- [Timed event functions](#timed-events)


---
## About

This package allows you to create bots (user bots) to monitor a stream. 

You will need to set up a 'user bot' account (a normal user account to act as a bot) and disable 2-factor 
authentication for the bot to be able to log in and handle commands / messages.

## Installation
```console
pip install kickbot
```

## Features

Currently supports the following features. More may be added soon, and contributions are more than welcome.

- Command handling: Handle commands, looking for the first word. i.e: ```'!hello'``` 
- Message handling: Handle messages, looking to match the full message. i.e: ```'hello world'```
- Sending messages: Have the bot send a message in chat
- Replying to messages: Reply directly to a users previous message / command.
- Access streamer and chat room information.
- Chat Moderation: Get info on users, ban users, timeout users.
- Timed events: Set a reoccurring event. i.e: Sending links to socials in chat every 30 minutes.

## Example

---

*Note*: For more examples, look in the [Examples Folder](/examples)
```python3
from kickbot import KickBot, KickMessage
from datetime import timedelta

    
async def send_links_in_chat(bot: KickBot):
    """ Timed event to send social links every 30 mins """
    links = "Youtube: https://youtube.com\n\nTwitch: https://twitch.tv"
    await bot.send_text(links)


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

    
async def ban_if_says_gay(bot: KickBot, message: KickMessage):
    """ Ban user for 20 minutes if they say 'your gay' """
    sender_username = message.sender.username
    ban_time = 20
    bot.moderator.timeout_user(sender_username, ban_time)

    
if __name__ == '__main__':
    USERBOT_EMAIL = "example@domain.com"
    USERBOT_PASS = "Password123"
    STREAMER = "streamer_username"
    
    bot = KickBot(USERBOT_EMAIL, USERBOT_PASS)
    bot.set_streamer(STREAMER)

    bot.add_command_handler('!following', time_following)
    bot.add_timed_event(timedelta(minutes=30), send_links_in_chat)
    bot.add_message_handler('your gay', ban_if_says_gay)
    
    bot.poll()
```
<br>

## Command and Message Handling


---
- Handler callback functions must be async
- Command handler looks to match the first word of the message / command.
- Message handler looks to match the full message.

### Paramaters
```python3
bot.add_message_handler('hello world', handle_hello_message)
bot.add_command_handler('!time', handle_time_command)
```

#### Command / Message paramater (type ```str```)

- The command / message to look for 

#### Callback function (type ```Callable```)
- Async callback function for the command  / message to trigger


### Handler Callback function parameters:
```python3
async def handle_hello_command(bot: KickBot, message: KickMessage):...
```


#### Bot parameter (type: ```KickBot```) 

- This will give you access to functions for the bot, such as ```bot.send_text```, and ```bot.reply_text```.
#### Message parameter (type: ```KickMessage```)
- This will give you access to all attributes of the message that triggered the handler. See [KickMessage](/kickbot/kick_message.py) for 
a full list of attributes.

Some useful message attributes include:
```python3
async def hello_handler(bot: KickBot, message: KickMessage):
    content = message.content # main message content
    args = message.args # list of arguments, i.e: ['!hello', 'how', 'are', 'you?']
    message_id = message.id # The uuid of the message
    
    # sender attributes
    sender_username = message.sender.username # username of the sender
    sender_user_id = message.sender.user_id # user ID if the sender
    seder_badges = message.sender.badges # badges of the sender
    
    response = f"Hello {sender_username}"
    await bot.reply_text(message, response)
```
<br>

## Sending Messages and Reply's

Functions mainly to be used inside a callback function, to send a message in chat, or reply to a users message.

### Messages:
```python
await bot.send_text(chat_message)
```

#### Chat Message Paramater: (type: ```str```)

- Message to be sent in chat


### Reply's:
```python3
await bot.reply_text(message, reply)
```

#### Message Paramater: (type: ```KickMessage```)

- The Message you want to reply to

#### Reply Paramater: (type: ```str```)

- The Reply to send to the Message

<br>

## Streamer and Chat Information
You can access information about the streamer, and chatroom via the ```bot.streamer_info``` , ```bot.chatroom_info```
and ```bot.chatroom_settings``` dictionaries.


Streamer Info: [Full Example](/examples/streamer_info_example.json)
```python
streamer_name = bot.streamer_name
follower_count = bot.streamer_info.get('followersCount')
streamer_user_id = bot.streamer_info.get('user_id')
```

Chatroom Info: [Full Example](/examples/chatroom_info_example.json)
```python
is_chat_slow_mode = bot.chatroom_info.get('slow_mode')
is_followers_only = bot.chatroom_info.get('followers_only')
is_subscribers_only = bot.chatroom_info.get('subscribers_only')
```

Chatroom Settings: [Full Example](/examples/chatroom_settings_example.json)
```python
links_allowed = bot.chatroom_settings.get('allow_link')
is_antibot_mode = bot.chatroom_settings.get('anti_bot_mode')
gifts_enabled = bot.chatroom_settings.get('gifts_enabled')
```

Bot Settings: [Full Example](examples/bot_settings_example.json)
```python
is_mod = bot.bot_settings.get('is_moderator')
is_admin = bot.bot_settings.get('is_admin')
```


#### Viewer Count

Access the current amount of viewers in the stream as an integer. 
```python
viewers = bot.current_viewers()
```
<br>

## Chat Moderation
*Note*: You must add the bot user as a moderator to access these functions.

All moderator functions are accessed using ```bot.moderator```



### Viewer User Info

```python
viewer_info = bot.moderator.get_viewer_info('user_username')
```

#### Paramater
```username``` type: ```str```

#### Returns
Dictionary containing viewer user info. [Full Example](examples/viewer_info_example.json)

<br>

### Timeout Ban
```python
bot.moderator.timeout_user('username', 20)
```

Ban a user for a certain amount of time.
#### Paramaters
```username``` type: ```str```: Username to be banned

```minutes``` type: ```int```: Time in minutes to ban the user for

#### Returns
```None```

<br>

### Permaban
```python
bot.moderator.permaban('username')
```
Permanently ban a user.
#### Paramater
```username``` type: ```str```: Username to ban permanently
#### Returns 
```None```

<br>

## Timed Events
Set a reoccurring function to be called, and the frequency to call the function.

i.e: Send links for your socials in chat every 30 minutes

### Parameters
```python3
bot.add_timed_event(timedelta(minutes=30), send_links_in_chat)
```

#### Frequency parameter (type: ```timedelta```)

- The frequency to call the function

#### Callback function (type: ```Callable```)

- Async callback function to be called with the frequency of the parameter above

### Timed Event Callback parameter

```python3
async def send_links_in_chat(bot: Kickbot):...
```

#### bot parameter (type: ```KickBot```)

- This will give you access to functions for the bot. For timed events, the most useful 
is ```bot.send_text``` to send a reoccurring message in chat

<br>