# bot.py - Controller bot using Pyrogram
import asyncio
import os
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from db import DBSessionManager
from userbots.wordchain_player import start_userbot
import config

app = Client("tnc_controller", bot_token=config.BOT_TOKEN, api_id=config.API_ID, api_hash=config.API_HASH)

db = DBSessionManager(config.DB_PATH)

@app.on_message(filters.command("start") & filters.private)
async def start_cmd(client, message):
    buttons = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("👑 Owner", url=f"tg://user?id={config.OWNER_ID}")],
            [
                InlineKeyboardButton("📢 Channel", url=config.SUPPORT_CHANNEL),
                InlineKeyboardButton("💬 Support", url=config.SUPPORT_CHAT)
            ],
        ]
    )
    await message.reply_photo(
        photo=config.START_IMAGE,
        caption=("🤖 Welcome to TNC WordChain Userbot!\n\n"
                 "Use /connect to store your Telethon string session and start a personal userbot that plays automatically."),
        reply_markup=buttons
    )

@app.on_message(filters.command("connect") & filters.private)
async def connect_cmd(client, message):
    await message.reply_text("Send your Telethon string session as a single message. It will be saved securely for you.")

@app.on_message(filters.private & filters.text)
async def receive_session(client, message):
    text = message.text.strip()
    # naive validation
    if len(text) < 20:
        await message.reply_text("That doesn't look like a valid string session. Please send the full string session.")
        return
    user_id = message.from_user.id
    db.save_session(user_id, text)
    await message.reply_text("✅ Saved your session. Starting your userbot...")
    # start userbot in background
    asyncio.create_task(start_userbot(text, user_id))
    await message.reply_text("✅ Userbot started. It will automatically join and play in wordchain games.")

def run():
    app.run()
