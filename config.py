# config.py — configuration loader
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Telegram API credentials
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
API_ID = int(os.getenv("API_ID", "29308061"))
API_HASH = os.getenv("API_HASH", "462de3dfc98fd938ef9c6ee31a72d099")

# File paths
WORDS_PATH = os.getenv("WORDS_PATH", "words.txt")
DB_PATH = os.getenv("DB_PATH", "sessions.db")

# Owner and support info
OWNER_ID = int(os.getenv("OWNER_ID", "8157752411"))
SUPPORT_CHAT = os.getenv("SUPPORT_CHAT", "https://t.me/TNCmeetup")
SUPPORT_CHANNEL = os.getenv("SUPPORT_CHANNEL", "https://t.me/TechNodeCoders")
START_IMAGE = os.getenv("START_IMAGE", "assets/start_banner.jpg")

# Optional: Logging & player options
LOG_GROUP_ID = int(os.getenv("LOG_GROUP_ID", "-1003111446920"))  # Set this to your private log group ID, or leave 0
PLAYER_NAME = os.getenv("PLAYER_NAME", "")  # Leave blank to auto-detect name