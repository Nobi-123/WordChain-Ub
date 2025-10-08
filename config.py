# config.py - Environment-based configuration
import os
from dotenv import load_dotenv

# Load environment variables from .env (optional on Heroku)
load_dotenv()

# ─── Telegram API ──────────────────────────────────────────────
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
API_ID = int(os.getenv("API_ID", "123456"))
API_HASH = os.getenv("API_HASH", "")

# ─── Database ──────────────────────────────────────────────────
# For MongoDB Atlas: e.g. mongodb+srv://user:pass@cluster.mongodb.net/tnc_wordchain
MONGO_URI = os.getenv("MONGO_URI", "")
DB_NAME = os.getenv("DB_NAME", "TNCWordChain")

# ─── WordChain Game ────────────────────────────────────────────
WORDS_PATH = os.getenv("WORDS_PATH", "words.txt")

# ─── Owner & Support ───────────────────────────────────────────
OWNER_ID = int(os.getenv("OWNER_ID", "8157752411"))
SUPPORT_CHAT = os.getenv("SUPPORT_CHAT", "https://t.me/TNCmeetup")
SUPPORT_CHANNEL = os.getenv("SUPPORT_CHANNEL", "https://t.me/TechNodeCoders")
LOG_GROUP_ID = int(os.getenv("LOG_GROUP_ID", "-1009999999999"))  # Add your log group ID here
START_IMAGE = os.getenv("START_IMAGE", "assets/start_banner.jpg")

# ─── Bot Settings ──────────────────────────────────────────────
ALLOWED_USERS = os.getenv("ALLOWED_USERS", "").split(",") if os.getenv("ALLOWED_USERS") else []
BOT_NAME = os.getenv("BOT_NAME", "TNC WordChain Bot")

# ─── Misc ──────────────────────────────────────────────────────
DEBUG = os.getenv("DEBUG", "False").lower() == "true"