# config.py - MongoDB compatible configuration
import os
from dotenv import load_dotenv
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
API_ID = int(os.getenv("API_ID", "29308061"))
API_HASH = os.getenv("API_HASH", "462de3dfc98fd938ef9c6ee31a72d099")

# MongoDB setup
MONGO_URI = os.getenv("MONGO_URI", "mongodb+srv://telegramescrower_db_user:EoWsXsfXtJrMb5GC@dkdk.sprm6ke.mongodb.net/?retryWrites=true&w=majority&appName=Dkdk")
DB_NAME = os.getenv("DB_NAME", "telegramescrower_db_user")

WORDS_PATH = os.getenv("WORDS_PATH", "words.txt")
OWNER_ID = int(os.getenv("OWNER_ID", "8157752411"))
LOG_GROUP_ID = int(os.getenv("LOG_GROUP_ID", "-1003111446920"))  # replace with your log group
SUPPORT_CHAT = os.getenv("SUPPORT_CHAT", "https://t.me/TNCmeetup")
SUPPORT_CHANNEL = os.getenv("SUPPORT_CHANNEL", "https://t.me/TechNodeCoders")
START_IMAGE = os.getenv("START_IMAGE", "assets/start_banner.jpg")