# main.py - Polling Version (More Reliable for Heroku)
import os
import logging
import asyncio
import sqlite3
from datetime import datetime
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.error import TelegramError, Forbidden, BadRequest

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class BotBroadcaster:
    def __init__(self, bot_token: str, admin_user_ids: list = None):
        """
        Initialize the bot broadcaster
        
        Args:
            bot_token: Your Telegram Bot Token
            admin_user_ids: List of admin user IDs who can send broadcasts
        """
        self.bot_token = bot_token
        self.admin_user_ids = admin_user_ids or []
        self.db_path = "bot_users.db"
        self.init_database()
    
    def init_database(self):
        """Initialize SQLite database to store user information"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT 1,
                last_interaction TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS broadcasts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message_text TEXT,
                sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                sent_by INTEGER,
                total_sent INTEGER,
                failed_sends INTEGER
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("Database initialized successfully")
    
    def add_user(self, user_id: int, username: str = None, first_name: str = None, last_name: str = None):
        """Add or update user in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO users 
            (user_id, username, first_name, last_name, last_interaction)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, username, first_name, last_name, datetime.now()))
        
        conn.commit()
        conn.close()
    
    def get_all_active_users(self):
        """Get all active users from database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT user_id FROM users WHERE is_active = 1')
        users = [row[0] for row in cursor.fetchall()]
        
        conn.close()
        return users
    
    def deactivate_user(self, user_id: int):
        """Mark user as inactive (blocked the bot)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('UPDATE users SET is_active = 0 WHERE user_id = ?', (user_id,))
        
        conn.commit()
        conn.close()
    
    async def broadcast_message(self, bot: Bot, message_text: str, sender_id: int = None, pin_message: bool = False):
        """
        Broadcast message to all active users
        
        Args:
            bot: Telegram Bot instance
            message_text: Message to broadcast
            sender_id: ID of user sending the broadcast
            pin_message: Whether to pin the message in private chats
        """
        users = self.get_all_active_users()
        successful_sends = 0
        failed_sends = 0
        
        logger.info(f"Starting broadcast to {len(users)} users")
        
        for user_id in users:
            try:
                # Send message
                sent_message = await bot.send_message(
                    chat_id=user_id,
                    text=message_text,
                    parse_mode='HTML'
                )
                
                # Pin message if requested (only works in groups/channels, not private chats)
                if pin_message:
                    try:
                        await bot.pin_chat_message(
                            chat_id=user_id,
                            message_id=sent_message.message_id,
                            disable_notification=True
                        )
                    except BadRequest as e:
                        logger.warning(f"Could not pin message for user {user_id}: {e}")
                
                successful_sends += 1
                logger.info(f"Message sent successfully to user {user_id}")
                
                # Small delay to avoid hitting rate limits
                await asyncio.sleep(0.05)
                
            except Forbidden:
                # User blocked the bot
                logger.warning(f"User {user_id} has blocked the bot")
                self.deactivate_user(user_id)
                failed_sends += 1
                
            except TelegramError as e:
                logger.error(f"Failed to send message to user {user_id}: {e}")
                failed_sends += 1
        
        # Log broadcast statistics
        self.log_broadcast(message_text, sender_id, successful_sends, failed_sends)
        
        logger.info(f"Broadcast completed. Sent: {successful_sends}, Failed: {failed_sends}")
        return successful_sends, failed_sends

    def log_broadcast(self, message_text: str, sent_by: int, total_sent: int, failed_sends: int):
        """Log broadcast statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO broadcasts (message_text, sent_by, total_sent, failed_sends)
            VALUES (?, ?, ?, ?)
        ''', (message_text, sent_by, total_sent, failed_sends))
        
        conn.commit()
        conn.close()

# Initialize global broadcaster variable
broadcaster = None

# Bot handlers
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command and add user to database"""
    user = update.effective_user
    
    # Add user to database
    broadcaster.add_user(
        user_id=user.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name
    )
    
    welcome_message = f"""
🤖 <b>Welcome {user.first_name}!</b>

Thank you for starting the bot! You'll now receive important updates and announcements.

Available commands:
• /start - Start the bot
• /help - Show help message
• /status - Check your status

<i>Bot is running on Heroku 🚀</i>
"""
    
    await update.message.reply_text(welcome_message, parse_mode='HTML')
    logger.info(f"New user registered: {user.id} ({user.first_name})")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command"""
    help_text = """
🆘 <b>Bot Help</b>

<b>User Commands:</b>
• /start - Start the bot and register for updates
• /help - Show this help message
• /status - Check your registration status

<b>Admin Commands:</b>
• /broadcast [message] - Send message to all users
• /pin_broadcast [message] - Send and pin message
• /stats - Show bot statistics
• /health - Check bot health

<i>You'll automatically receive important bot updates!</i>
"""
    
    await update.message.reply_text(help_text, parse_mode='HTML')

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /status command"""
    user_id = update.effective_user.id
    users = broadcaster.get_all_active_users()
    
    if user_id in users:
        status_text = "✅ You are registered and will receive bot updates!"
    else:
        status_text = "❌ You are not registered. Send /start to register for updates."
    
    await update.message.reply_text(status_text)

async def health_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /health command (admin only) - Check bot health"""
    user_id = update.effective_user.id
    
    if user_id not in broadcaster.admin_user_ids:
        await update.message.reply_text("❌ You don't have permission to use this command.")
        return
    
    try:
        # Check database connection
        conn = sqlite3.connect(broadcaster.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM users')
        user_count = cursor.fetchone()[0]
        conn.close()
        
        health_text = f"""
💚 <b>Bot Health Check</b>

✅ Database: Connected
✅ Bot: Running (Polling Mode)
👥 Total Users: {user_count}
🌐 Environment: Heroku
⏰ Status: All systems operational

<i>Bot is healthy and running smoothly!</i>
"""
        
        await update.message.reply_text(health_text, parse_mode='HTML')
        
    except Exception as e:
        error_text = f"""
❤️‍🩹 <b>Bot Health Check</b>

❌ Error detected: {str(e)}

<i>Please check logs for details.</i>
"""
        await update.message.reply_text(error_text, parse_mode='HTML')
        logger.error(f"Health check failed: {e}")

async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /broadcast command (admin only)"""
    user_id = update.effective_user.id
    
    if user_id not in broadcaster.admin_user_ids:
        await update.message.reply_text("❌ You don't have permission to use this command.")
        return
    
    if not context.args:
        await update.message.reply_text("Please provide a message to broadcast.\n\nUsage: /broadcast Your message here")
        return
    
    message_text = ' '.join(context.args)
    
    # Add broadcast header
    broadcast_message = f"""
📢 <b>Important Bot Update</b>

{message_text}

<i>This is an automated message from the bot admin.</i>
"""
    
    await update.message.reply_text("🔄 Starting broadcast...")
    
    successful, failed = await broadcaster.broadcast_message(
        bot=context.bot,
        message_text=broadcast_message,
        sender_id=user_id
    )
    
    result_text = f"""
📊 <b>Broadcast Results</b>

✅ Successfully sent: {successful}
❌ Failed to send: {failed}
📱 Total attempts: {successful + failed}
"""
    
    await update.message.reply_text(result_text, parse_mode='HTML')

async def pin_broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /pin_broadcast command (admin only)"""
    user_id = update.effective_user.id
    
    if user_id not in broadcaster.admin_user_ids:
        await update.message.reply_text("❌ You don't have permission to use this command.")
        return
    
    if not context.args:
        await update.message.reply_text("Please provide a message to broadcast and pin.\n\nUsage: /pin_broadcast Your important message")
        return
    
    message_text = ' '.join(context.args)
    
    # Add important update header
    broadcast_message = f"""
📌 <b>IMPORTANT BOT UPDATE</b>

{message_text}

⚠️ <i>This message has been pinned due to its importance.</i>
"""
    
    await update.message.reply_text("🔄 Starting broadcast with pin...")
    
    successful, failed = await broadcaster.broadcast_message(
        bot=context.bot,
        message_text=broadcast_message,
        sender_id=user_id,
        pin_message=True
    )
    
    result_text = f"""
📊 <b>Pin Broadcast Results</b>

✅ Successfully sent: {successful}
❌ Failed to send: {failed}
📱 Total attempts: {successful + failed}
📌 Pin attempts: {successful} (pins may fail in private chats)
"""
    
    await update.message.reply_text(result_text, parse_mode='HTML')

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /stats command (admin only)"""
    user_id = update.effective_user.id
    
    if user_id not in broadcaster.admin_user_ids:
        await update.message.reply_text("❌ You don't have permission to use this command.")
        return
    
    conn = sqlite3.connect(broadcaster.db_path)
    cursor = conn.cursor()
    
    # Get user statistics
    cursor.execute('SELECT COUNT(*) FROM users WHERE is_active = 1')
    active_users = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM users WHERE is_active = 0')
    inactive_users = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM broadcasts')
    total_broadcasts = cursor.fetchone()[0]
    
    # Get latest broadcast info
    cursor.execute('''
        SELECT sent_at, total_sent, failed_sends 
        FROM broadcasts 
        ORDER BY sent_at DESC 
        LIMIT 1
    ''')
    latest_broadcast = cursor.fetchone()
    
    conn.close()
    
    latest_info = ""
    if latest_broadcast:
        latest_info = f"\n📡 Last broadcast: {latest_broadcast[0]}\n   Sent: {latest_broadcast[1]}, Failed: {latest_broadcast[2]}"
    
    stats_text = f"""
📊 <b>Bot Statistics</b>

👥 Active Users: {active_users}
🚫 Inactive Users: {inactive_users}
📢 Total Broadcasts: {total_broadcasts}
📱 Total Users: {active_users + inactive_users}
🌐 Environment: Heroku (Polling){latest_info}

<i>Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</i>
"""
    
    await update.message.reply_text(stats_text, parse_mode='HTML')

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle regular messages and update user activity"""
    user = update.effective_user
    
    # Update user activity
    broadcaster.add_user(
        user_id=user.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name
    )

async def keep_alive():
    """Keep the bot alive on Heroku"""
    while True:
        try:
            logger.info("Bot is alive and running...")
            await asyncio.sleep(300)  # Log every 5 minutes
        except Exception as e:
            logger.error(f"Keep alive error: {e}")
            await asyncio.sleep(60)

def main():
    """Main function to run the bot"""
    # Get configuration from environment variables
    BOT_TOKEN = os.getenv('BOT_TOKEN')
    ADMIN_USER_IDS_STR = os.getenv('ADMIN_USER_IDS', '')
    PORT = int(os.getenv('PORT', 8080))
    
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN environment variable is required!")
        return
    
    # Parse admin user IDs
    ADMIN_USER_IDS = []
    if ADMIN_USER_IDS_STR:
        try:
            ADMIN_USER_IDS = [int(uid.strip()) for uid in ADMIN_USER_IDS_STR.split(',') if uid.strip()]
        except ValueError:
            logger.error("Invalid ADMIN_USER_IDS format. Use comma-separated integers.")
            return
    
    logger.info(f"Starting bot with {len(ADMIN_USER_IDS)} admin users")
    
    global broadcaster
    broadcaster = BotBroadcaster(BOT_TOKEN, ADMIN_USER_IDS)
    
    # Create application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(CommandHandler("health", health_command))
    application.add_handler(CommandHandler("broadcast", broadcast_command))
    application.add_handler(CommandHandler("pin_broadcast", pin_broadcast_command))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Start the bot with polling (more reliable for Heroku)
    logger.info(f"Bot starting with polling mode on port {PORT}")
    
    # Use polling mode which is more reliable on Heroku
    application.run_polling(
        drop_pending_updates=True,
        timeout=30,
        bootstrap_retries=3,
        read_timeout=30,
        write_timeout=30,
        connect_timeout=30,
        pool_timeout=30
    )

if __name__ == "__main__":
    main()
