import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Bot Configuration
BOT_TOKEN = os.getenv("BOT_TOKEN")
API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH")
OWNER_ID = int(os.getenv("OWNER_ID", "0"))

# Database Configuration
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("DATABASE_NAME", "broadcast_bot")

# Validate required environment variables
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN environment variable is required!")

if not API_ID or API_ID == 0:
    raise ValueError("API_ID environment variable is required!")

if not API_HASH:
    raise ValueError("API_HASH environment variable is required!")

if not OWNER_ID or OWNER_ID == 0:
    raise ValueError("OWNER_ID environment variable is required!")
