# Import necessary libraries
import logging
import asyncio
from telethon import TelegramClient, events
from decouple import config
from telethon.tl.functions.users import GetFullUserRequest
from telethon.errors.rpcerrorlist import UsernameNotOccupiedError, UserIdInvalidError

# Configure logging for warnings only
logging.basicConfig(format='[%(levelname)s/%(asctime)s] %(name)s: %(message)s', level=logging.WARNING)

# Load API credentials from environment variables
api_id = config("APP_ID")
api_hash = config("API_HASH")
bot_token = config("BOT_TOKEN")

# Create a Telegram client for the bot
msg_frwd = TelegramClient('bot', api_id, api_hash).start(bot_token=bot_token)

# Function to handle "/start" command
@msg_frwd.on(events.NewMessage(pattern="/start"))
async def start_handler(event):
    """
    Greets the user, introduces the bot, and provides instructions on how to get help.
    """
    # Get user information
    user = await msg_frwd(GetFullUserRequest(event.sender_id))

    # Send introductory message
    await event.reply(f"Hi {user.user.first_name}, I am a message forwarder bot.\nRead /help for more!\n\n(c) @its_xditya")

# Function to handle "/help" command
@msg_frwd.on(events.NewMessage(pattern="/help"))
async def help_handler(event):
    """
    Provides instructions on how to use the bot to forward messages between groups.
    """
    # Send help message
    await event.reply("I forward messages from one group to another.\nAdd me to both the groups first...\nUse `/frwd <to group id/username> <message/reply to message>` to forward the message to that group.\n\n(c) @its_xditya")

# Function to handle "/frwd" command and message forwarding
@msg_frwd.on(events.NewMessage(pattern="/frwd"))
async def forward_handler(event):
    """
    Forwards messages from a user in a group chat to another group chat, 
    provided the bot is present in both groups.

    Checks for errors and provides informative messages to the user.
    """
    # Check if the command is used in a private chat
    if event.is_private:
        await event.reply("I work in groups!")
        return

    # Get user information
    user = await msg_frwd(GetFullUserRequest(event.sender_id))

    # Split the command text to extract arguments
    text_parts = event.text.split(" ", maxsplit=2)

    try:
        # Extract chat ID/username and message from arguments
        chat_id_or_username = text_parts[1]
        message_to_forward = text_parts[2]

        # Check if message is provided
        if message_to_forward is None:
            await event.reply("No message provided!\n\nFormat - `/frwd <chat id/username> <message/reply to message>`")
            return

        # Handle usernames by converting them to chat IDs
        if chat_id_or_username.startswith('@'):
            try:
                chat_entity = await msg_frwd.get_entity(chat_id_or_username)
                chat_id = chat_entity.id
            except UsernameNotOccupiedError as e:
                await event.reply("Username not found! Please check the username and try again.")
                return
            except UserIdInvalidError as e:
                await event.reply("Invalid user ID! Please check the user ID and try again.")
                return
        else:
            chat_id = int(chat_id_or_username)
        
        # Potential bug fix: Check if the message is a reply to another message 
        # and forward the replied message instead if applicable
        if event.is_reply:
            # Get the replied message
            replied_message = await event.get_reply_message()
            # If there's a replied message, forward that instead
            if replied_message:
                message_to_forward = replied_message.message

        # Attempt to forward the message
        try:
            # Send the message to the target group chat
            sent_message = await msg_frwd.send_message(chat_id, message_to_forward)

            # Reply to the user with confirmation and sender information
            await sent_message.reply(f"Message from [{user.user.first_name}](tg://user?id={event.sender_id}) forwarded successfully.")
        
        except Exception as e:
            await event.reply(f"Failed to forward the message. Error: {str(e)}")
    
    except IndexError:
        await event.reply("Invalid command format!\n\nFormat - `/frwd <chat id/username> <message/reply to message>`")
    except Exception as e:
        await event.reply(f"An unexpected error occurred: {str(e)}")

# Start the Telegram client
if __name__ == "__main__":
    with msg_frwd:
        msg_frwd.run_until_disconnected()
