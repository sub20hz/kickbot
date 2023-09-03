# kickbot

---
### A python package to create bots for kick.com

## About

---
This package allows you to create bots (user bots) to monitor a stream. 

You will need to set up a 'user bot' account (a normal user account to act as a bot) and disable 2-factor authentication for the bot to be able to login and handle commands / messages.

## Installation
```console
pip install kickbot
```

## Usage

---
Currently supports handling messages and commands, replying to them, and sending messages in chat.

More features will be added, and Contributions are more than welcome.

```python3
from kickbot import KickBot, KickMessage
from datetime import datetime


async def handle_hello_message(bot: KickBot, message: KickMessage):
    content = message.content
    sender_username = message.sender.username
    response = f"Hello {sender_username}. Got your message {content}"
    await bot.send_text(response)

    
async def handle_goodbye_command(bot: KickBot, message: KickMessage):
    reply_message = f"Goodbye {message.sender.username}"
    await bot.reply_text(message, reply_message)

    
async def handle_time_command(bot: KickBot, messsage: KickMessage):
    time = str(datetime.utcnow())
    response = f"Current UTC Time: {time}"
    await bot.send_text(response)


if __name__ == '__main__':
    USERBOT_EMAIL = "example@domain.com"
    USERBOT_PASS = "Password123"
    STREAMER = "streamer_username"
    
    bot = KickBot(USERBOT_EMAIL, USERBOT_PASS)
    bot.set_streamer(STREAMER)

    bot.add_message_handler('hello world', handle_hello_message)
    bot.add_command_handler('!goodbye', handle_goodbye_command)
    bot.add_command_handler('!time', handle_time_command)

    bot.poll()
```
## Command and Message Handling

---
- Handler functions must be async
- Command handler looks to match the first word of the message / command.
- Message handler looks to match the full message.


### Required Parameters:
```python3
async def handle_hello_command(bot: KickBot, message: KickMessage):...
```


#### Bot parameter (type: ```KickBot```) 

- This will give you access to functions for the bot, such as ```bot.send_text```, and ```bot.reply_text```.
#### Message parameter (type: ```KickMessage```)
- This will give you access to all attributes of the message that triggered the handler. See [KickMessage]() for 
a full list of attributes.

- Some usefule message attributes include:
```python3
async def hello_handler(bot: KickBot, message: KickMessage):
    content = message.content
    args = message.args
    message_id = message.id
    
    sender_username = message.sender.username
    sender_user_id = = message.sender.user_id
    seder_badges = message.sender.badges
    
    response = f"Hello {sender_username}"
    await bot.reply_text(message, response)
```
