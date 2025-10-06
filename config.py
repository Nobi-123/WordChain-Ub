# config.py - configuration loaded from environment
import os
from dotenv import load_dotenv
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH", "")

WORDS_PATH = os.getenv("WORDS_PATH", "words.txt")
DB_PATH = os.getenv("DB_PATH", "sessions.db")

OWNER_ID = int(os.getenv("OWNER_ID", "123456789"))
SUPPORT_CHAT = os.getenv("SUPPORT_CHAT", "https://t.me/TNCChat")
SUPPORT_CHANNEL = os.getenv("SUPPORT_CHANNEL", "https://t.me/TNCUpdates")
START_IMAGE = os.getenv("START_IMAGE", "assets/start_banner.jpg")
