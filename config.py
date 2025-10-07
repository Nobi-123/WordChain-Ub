# config.py - configuration loaded from environment
import os
from dotenv import load_dotenv
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "7988359152:AAFTDV1NFLuO_tUldwbTP_H2ZtIfp_SDFqo")
API_ID = int(os.getenv("API_ID", "29308061"))
API_HASH = os.getenv("API_HASH", "462de3dfc98fd938ef9c6ee31a72d099")

WORDS_PATH = os.getenv("WORDS_PATH", "words.txt")
DB_PATH = os.getenv("DB_PATH", "sessions.db")

OWNER_ID = int(os.getenv("OWNER_ID", "8315954262"))
SUPPORT_CHAT = os.getenv("SUPPORT_CHAT", "https://t.me/TNCmeetup")
SUPPORT_CHANNEL = os.getenv("SUPPORT_CHANNEL", "https://t.me/TechNodeCoders")
START_IMAGE = os.getenv("START_IMAGE", "assets/start_banner.jpg")
