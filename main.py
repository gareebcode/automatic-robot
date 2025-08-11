# main.py
import os
import asyncio
import logging
import traceback
from pyrogram import Client, filters
from pyrogram.errors import FloodWait, InputUserDeactivated, UserIsBlocked, PeerIdInvalid
from config import OWNER_ID, BOT_TOKEN, API_ID, API_HASH
from core.mongo.users_db import get_users, add_user

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Initialize Pyrogram client
app = Client(
    "broadcast_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    workers=100
)

async def send_msg(user_id, message):
    """Send message to a user with auto-pin functionality"""
    try:
        x = await message.copy(chat_id=user_id)
        try:
            await x.pin()
        except Exception:
            try:
                await x.pin(both_sides=True)
            except Exception:
                pass  # Pin failed, continue without error
        return 200, None
    except FloodWait as e:
        logger.warning(f"FloodWait: {e.value} seconds for user {user_id}")
        await asyncio.sleep(e.value)
        return await send_msg(user_id, message)
    except InputUserDeactivated:
        return 400, f"{user_id} : deactivated\n"
    except UserIsBlocked:
        return 400, f"{user_id} : blocked the bot\n"
    except PeerIdInvalid:
        return 400, f"{user_id} : user id invalid\n"
    except Exception as e:
        return 500, f"{user_id} : {str(e)}\n"

@app.on_message(filters.command("start"))
async def start_command(client, message):
    """Handle /start command and register user"""
    user_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name
    
    # Add user to database
    await add_user(user_id, username, first_name)
    
    welcome_text = f"""
🤖 **Welcome {first_name}!**

Thank you for starting the bot! You'll now receive important updates and announcements.

**Available Commands:**
• /start - Start the bot
• /help - Show help message
• /status - Check your status

*Bot is running on Heroku 🚀*
"""
    
    await message.reply_text(welcome_text)
    logger.info(f"New user registered: {user_id} ({first_name})")

@app.on_message(filters.command("help"))
async def help_command(client, message):
    """Handle /help command"""
    help_text = """
🆘 **Bot Help**

**User Commands:**
• /start - Start the bot and register for updates
• /help - Show this help message  
• /status - Check your registration status

**Admin Commands (Owner Only):**
• /gcast - Broadcast message with auto-pin (reply to message)
• /announce - Forward message to all users (reply to message)
• /stats - Show bot statistics
• /users - Get total user count

*You'll automatically receive important bot updates!*
"""
    
    await message.reply_text(help_text)

@app.on_message(filters.command("status"))
async def status_command(client, message):
    """Handle /status command"""
    user_id = message.from_user.id
    users = await get_users() or []
    
    if user_id in users:
        status_text = "✅ You are registered and will receive bot updates!"
    else:
        status_text = "❌ You are not registered. Send /start to register for updates."
        # Auto-register the user
        await add_user(user_id, message.from_user.username, message.from_user.first_name)
        status_text += "\n\n🔄 You have been automatically registered!"
    
    await message.reply_text(status_text)

@app.on_message(filters.command("gcast") & filters.user(OWNER_ID))
async def broadcast(client, message):
    """Broadcast message with auto-pin functionality"""
    if not message.reply_to_message:
        await message.reply_text("🔄 **ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴍᴇssᴀɢᴇ ᴛᴏ ʙʀᴏᴀᴅᴄᴀsᴛ ɪᴛ.**")
        return
    
    exmsg = await message.reply_text("📡 **sᴛᴀʀᴛᴇᴅ ʙʀᴏᴀᴅᴄᴀsᴛɪɴɢ!**")
    all_users = await get_users() or []
    done_users = 0
    failed_users = 0
    
    logger.info(f"Starting broadcast to {len(all_users)} users")
    
    for user in all_users:
        try:
            status_code, error = await send_msg(user, message.reply_to_message)
            if status_code == 200:
                done_users += 1
            else:
                failed_users += 1
                if error:
                    logger.warning(f"Failed to send to {user}: {error}")
            
            await asyncio.sleep(0.1)  # Rate limiting
        except Exception as e:
            failed_users += 1
            logger.error(f"Broadcast error for user {user}: {e}")
    
    # Update broadcast results
    if failed_users == 0:
        result_text = f"""
📊 **sᴜᴄᴄᴇssғᴜʟʟʏ ʙʀᴏᴀᴅᴄᴀsᴛɪɴɢ ✅**

**sᴇɴᴛ ᴍᴇssᴀɢᴇ ᴛᴏ** `{done_users}` **ᴜsᴇʀs**
📌 **Messages automatically pinned**
"""
    else:
        result_text = f"""
📊 **sᴜᴄᴄᴇssғᴜʟʟʏ ʙʀᴏᴀᴅᴄᴀsᴛɪɴɢ ✅**

**sᴇɴᴛ ᴍᴇssᴀɢᴇ ᴛᴏ** `{done_users}` **ᴜsᴇʀs**
📌 **Messages automatically pinned**

**ɴᴏᴛᴇ:** `ᴅᴜᴇ ᴛᴏ sᴏᴍᴇ ɪssᴜᴇ ᴄᴀɴ'ᴛ ᴀʙʟᴇ ᴛᴏ ʙʀᴏᴀᴅᴄᴀsᴛ` `{failed_users}` **ᴜsᴇʀs**
"""
    
    await exmsg.edit_text(result_text)
    logger.info(f"Broadcast completed. Sent: {done_users}, Failed: {failed_users}")

@app.on_message(filters.command("announce") & filters.user(OWNER_ID))
async def announced(client, message):
    """Forward message to all users"""
    if not message.reply_to_message:
        return await message.reply_text("📝 **Reply To Some Post To Broadcast**")
    
    to_send = message.reply_to_message.id
    exmsg = await message.reply_text("📢 **sᴛᴀʀᴛᴇᴅ ᴀɴɴᴏᴜɴᴄᴇᴍᴇɴᴛ!**")
    users = await get_users() or []
    
    logger.info(f"Starting announcement to {len(users)} users")
    
    done_users = 0
    failed_users = 0
    
    for user in users:
        try:
            await client.forward_messages(
                chat_id=int(user),
                from_chat_id=message.chat.id,
                message_ids=to_send
            )
            done_users += 1
            await asyncio.sleep(0.1)  # Rate limiting
        except FloodWait as e:
            logger.warning(f"FloodWait: {e.value} seconds")
            await asyncio.sleep(e.value)
            # Retry the message
            try:
                await client.forward_messages(
                    chat_id=int(user),
                    from_chat_id=message.chat.id,
                    message_ids=to_send
                )
                done_users += 1
            except Exception:
                failed_users += 1
        except Exception as e:
            failed_users += 1
            logger.error(f"Failed to announce to {user}: {e}")
    
    # Update announcement results
    if failed_users == 0:
        result_text = f"""
📊 **sᴜᴄᴄᴇssғᴜʟʟʏ ᴀɴɴᴏᴜɴᴄᴇᴍᴇɴᴛ ✅**

**ғᴏʀᴡᴀʀᴅᴇᴅ ᴍᴇssᴀɢᴇ ᴛᴏ** `{done_users}` **ᴜsᴇʀs**
"""
    else:
        result_text = f"""
📊 **sᴜᴄᴄᴇssғᴜʟʟʏ ᴀɴɴᴏᴜɴᴄᴇᴍᴇɴᴛ ✅**

**ғᴏʀᴡᴀʀᴅᴇᴅ ᴍᴇssᴀɢᴇ ᴛᴏ** `{done_users}` **ᴜsᴇʀs**

**ɴᴏᴛᴇ:** `ᴅᴜᴇ ᴛᴏ sᴏᴍᴇ ɪssᴜᴇ ᴄᴀɴ'ᴛ ᴀʙʟᴇ ᴛᴏ ᴀɴɴᴏᴜɴᴄᴇ` `{failed_users}` **ᴜsᴇʀs**
"""
    
    await exmsg.edit_text(result_text)
    logger.info(f"Announcement completed. Sent: {done_users}, Failed: {failed_users}")

@app.on_message(filters.command("stats") & filters.user(OWNER_ID))
async def stats_command(client, message):
    """Show bot statistics"""
    users = await get_users() or []
    total_users = len(users)
    
    stats_text = f"""
📊 **Bot Statistics**

👥 **Total Users:** `{total_users}`
🤖 **Bot Status:** Active
🌐 **Environment:** Heroku
⚡ **Library:** Pyrogram

*Last updated: Now*
"""
    
    await message.reply_text(stats_text)

@app.on_message(filters.command("users") & filters.user(OWNER_ID))
async def users_command(client, message):
    """Get total user count"""
    users = await get_users() or []
    await message.reply_text(f"👥 **Total Users:** `{len(users)}`")

@app.on_message(filters.private)
async def handle_private_messages(client, message):
    """Handle all private messages and register users"""
    user_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name
    
    # Auto-register user on any interaction
    await add_user(user_id, username, first_name)

async def keep_alive():
    """Keep the bot alive on Heroku"""
    while True:
        try:
            logger.info("Bot is alive and running...")
            await asyncio.sleep(300)  # Log every 5 minutes
        except Exception as e:
            logger.error(f"Keep alive error: {e}")
            await asyncio.sleep(60)

async def main():
    """Main function to start the bot"""
    try:
        logger.info("Starting Pyrogram bot...")
        await app.start()
        logger.info("Bot started successfully!")
        
        # Start keep alive task
        asyncio.create_task(keep_alive())
        
        # Keep the bot running
        await asyncio.Event().wait()
        
    except Exception as e:
        logger.error(f"Bot startup error: {e}")
    finally:
        await app.stop()

if __name__ == "__main__":
    asyncio.run(main())
