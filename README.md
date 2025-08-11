# Telegram Broadcast Bot

A powerful Telegram bot for broadcasting messages to users with automatic pinning functionality. Perfect for sending important updates, announcements, and notifications to all your bot users.

## Features

- 🤖 **Auto User Registration**: Users are automatically registered when they start the bot
- 📢 **Broadcast Messages**: Send messages to all registered users
- 📌 **Auto Pin Messages**: Automatically pin important updates
- 👑 **Admin Controls**: Special commands for authorized administrators
- 📊 **Statistics**: Track user counts and broadcast success rates
- 🗃️ **Database**: SQLite database for user management
- ☁️ **Heroku Ready**: Optimized for Heroku deployment

## Commands

### User Commands
- `/start` - Start the bot and register for updates
- `/help` - Show help message
- `/status` - Check registration status

### Admin Commands
- `/broadcast [message]` - Send message to all users
- `/pin_broadcast [message]` - Send and pin important message
- `/stats` - Show bot statistics
- `/health` - Check bot health status

## Quick Deploy to Heroku

[![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy)

## Manual Deployment to Heroku

### Prerequisites
- [Heroku account](https://signup.heroku.com/)
- [Heroku CLI](https://devcenter.heroku.com/articles/heroku-cli)
- Telegram Bot Token (get from [@BotFather](https://t.me/botfather))
- Your Telegram User ID (get from [@userinfobot](https://t.me/userinfobot))

### Step 1: Create Your Bot
1. Message [@BotFather](https://t.me/botfather) on Telegram
2. Send `/newbot` and follow instructions
3. Save your bot token

### Step 2: Get Your User ID
1. Message [@userinfobot](https://t.me/userinfobot) on Telegram
2. Note your user ID for admin access

### Step 3: Deploy to Heroku

#### Option A: Using Heroku CLI
```bash
# Clone or download this repository
git clone <repository-url>
cd telegram-broadcast-bot

# Login to Heroku
heroku login

# Create new Heroku app
heroku create your-bot-name

# Set environment variables
heroku config:set BOT_TOKEN="your_bot_token_here"
heroku config:set ADMIN_USER_IDS="your_user_id,another_admin_id"
heroku config:set HEROKU_APP_NAME="your-bot-name"

# Deploy to Heroku
git add .
git commit -m "Initial deployment"
git push heroku main
```

#### Option B: Using Heroku Dashboard
1. Fork this repository
2. Connect your GitHub account to Heroku
3. Create new app and connect to your forked repository
4. Set environment variables in Settings > Config Vars:
   - `BOT_TOKEN`: Your bot token
   - `ADMIN_USER_IDS`: Comma-separated admin user IDs
   - `HEROKU_APP_NAME`: Your Heroku app name
5. Deploy from the Deploy tab

### Step 4: Set Webhook
The bot automatically configures webhooks for Heroku deployment. No manual webhook setup required!

## Local Development

### Setup
```bash
# Clone repository
git clone <repository-url>
cd telegram-broadcast-bot

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env

# Edit .env file with your bot token and admin IDs
```

### Run Locally
```bash
python main.py
```

For local development, the bot uses polling mode instead of webhooks.

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `BOT_TOKEN` | Your Telegram bot token from BotFather | Yes |
| `ADMIN_USER_IDS` | Comma-separated list of admin user IDs | Yes |
| `HEROKU_APP_NAME` | Your Heroku app name (auto-set by Heroku) | No |
| `PORT` | Port number (auto-set by Heroku) | No |

## File Structure

```
telegram-broadcast-bot/
├── main.py              # Main bot application
├── requirements.txt     # Python dependencies
├── Procfile            # Heroku process configuration
├── runtime.txt         # Python version specification
├── app.json           # Heroku deployment configuration
├── .env.example       # Environment variables template
├── README.md          # This file
└── bot_users.db       # SQLite database (created automatically)
```

## Usage Examples

### Broadcasting a Message
```
/broadcast Hello everyone! We have a new feature update available. 🚀
```

### Pinning an Important Message
```
/pin_broadcast ⚠️ Maintenance scheduled for tomorrow at 2 PM UTC. The bot will be unavailable for 30 minutes.
```

### Checking Statistics
```
/stats
```

## Database Schema

The bot uses SQLite with two main tables:

### Users Table
- `user_id`: Unique Telegram user ID
- `username`: User's Telegram username
- `first_name`: User's first name
- `last_name`: User's last name
- `started_at`: When user first started the bot
- `is_active`: Whether user is still active
- `last_interaction`: Last time user interacted with bot

### Broadcasts Table
- `id`: Unique broadcast ID
- `message_text`: The broadcast message
- `sent_at`: When broadcast was sent
- `sent_by`: Admin user ID who sent it
- `total_sent`: Number of successful sends
- `failed_sends`: Number of failed sends

## Features in Detail

### User Management
- Automatically registers users when they send `/start`
- Tracks user activity and interaction timestamps
- Handles blocked users gracefully
- Maintains active/inactive user status

### Broadcasting System
- Sends messages to all active users
- Handles rate limiting automatically
- Provides detailed success/failure statistics
- Logs all broadcasts for audit purposes

### Admin Controls
- Role-based access control for admin commands
- Health monitoring and statistics
- Broadcast management and tracking

### Error Handling
- Graceful handling of blocked users
- Rate limit management
- Database error recovery
- Comprehensive logging

## Monitoring and Logs

### View Heroku Logs
```bash
heroku logs --tail -a your-app-name
```

### Health Check
Admins can use `/health` command to check bot status and database connectivity.

## Troubleshooting

### Common Issues

1. **Bot not responding**: Check if webhook is set correctly
2. **Broadcast failing**: Verify admin user IDs are correct
3. **Database errors**: Check Heroku logs for details
4. **Environment variables**: Ensure all required vars are set

### Debug Commands
- `/health` - Check bot health (admin only)
- `/stats` - View user and broadcast statistics
- Check Heroku logs for detailed error information

## Security Considerations

- Admin user IDs are stored as environment variables
- Database is local SQLite (consider PostgreSQL for production)
- Bot token should never be committed to repository
- Use environment variables for all sensitive data

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

If you encounter any issues or have questions:
1. Check the troubleshooting section
2. Review Heroku logs
3. Open an issue on GitHub

## Changelog

### Version 1.0.0
- Initial release
- Basic broadcast functionality
- Auto-pin messages
- Heroku deployment support
- User management system
- Admin controls and statistics
