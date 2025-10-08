# config.py - MongoDB compatible configuration
import os
from dotenv import load_dotenv

# Load environment variables (for Heroku or local .env)
load_dotenv()

# ─── Telegram API Credentials ───
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
API_ID = int(os.getenv("API_ID", "29308061"))
API_HASH = os.getenv("API_HASH", "462de3dfc98fd938ef9c6ee31a72d099")

# ─── MongoDB Setup ───
MONGO_URI = os.getenv(
    "MONGO_URI",
    "mongodb+srv://telegramescrower_db_user:EoWsXsfXtJrMb5GC@dkdk.sprm6ke.mongodb.net/?retryWrites=true&w=majority&appName=Dkdk",
)
DB_NAME = os.getenv("DB_NAME", "TNC_WordChainDB")

# ─── Owner and Support Info ───
OWNER_ID = int(os.getenv("OWNER_ID", "8157752411"))
SUPPORT_CHAT = os.getenv("SUPPORT_CHAT", "https://t.me/TNCmeetup")
SUPPORT_CHANNEL = os.getenv("SUPPORT_CHANNEL", "https://t.me/TechNodeCoders")

# ─── Log and Game Settings ───
LOG_GROUP_ID = int(os.getenv("LOG_GROUP_ID", "-1003111446920"))
WORDS_PATH = os.getenv("WORDS_PATH", "words.txt")
START_IMAGE = os.getenv("START_IMAGE", "assets/start_banner.jpg")

# ─── Optional: Group where the WordChain game runs ───
WORDCHAIN_GROUP = int(os.getenv("WORDCHAIN_GROUP", "-1003111446920"))