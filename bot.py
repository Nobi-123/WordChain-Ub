# bot.py — Controller bot using Pyrogram
import asyncio
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from db import DBSessionManager
from userbots.wordchain_player import start_userbot
import config

# Initialize Pyrogram bot
app = Client(
    "tnc_controller",
    bot_token=config.BOT_TOKEN,
    api_id=config.API_ID,
    api_hash=config.API_HASH
)

# Initialize database manager
db = DBSessionManager(config.DB_PATH)


# -----------------------
# /start command
# -----------------------
@app.on_message(filters.command("start") & filters.private)
async def start_cmd(client, message):
    buttons = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("👑 Owner", url=f"tg://user?id={config.OWNER_ID}")],
            [
                InlineKeyboardButton("📢 Channel", url=config.SUPPORT_CHANNEL),
                InlineKeyboardButton("💬 Support Chat", url=config.SUPPORT_CHAT)
            ],
        ]
    )
    await message.reply_photo(
        photo=config.START_IMAGE,
        caption=(
            "🤖 **Welcome to TNC WordChain Userbot!**\n\n"
            "💡 This bot allows you to connect your Telethon string session and let it play "
            "WordChain games automatically for you.\n\n"
            "To begin, send your **Telethon string session** using the `/connect` command."
        ),
        reply_markup=buttons
    )


# -----------------------
# /connect command
# -----------------------
@app.on_message(filters.command("connect") & filters.private)
async def connect_cmd(client, message):
    await message.reply_text(
        "🔗 Please send your **Telethon string session**.\n\n"
        "Make sure you copy the entire string — it usually starts with `1A` or `BQAA...`"
    )


# -----------------------
# Handle received string sessions
# -----------------------
@app.on_message(filters.private & ~filters.command(["start", "connect", "broadcast"]) & filters.text)
async def receive_session(client, message):
    text = message.text.strip()
    user_id = message.from_user.id

    # Quick validation
    if len(text) < 50:
        await message.reply_text("⚠️ That doesn’t look like a valid Telethon string session.\nPlease send the full session string.")
        return

    # Save to DB
    db.save_session(user_id, text)
    await message.reply_text("✅ Saved your session. Starting your userbot...")

    # Start userbot safely in the background
    asyncio.create_task(start_userbot(text, user_id))
    await message.reply_text("🟢 Your userbot is now running!\n\nYou can play WordChain in any group, and it will respond automatically on your turns.")


# -----------------------
# /broadcast command (owner only)
# -----------------------
@app.on_message(filters.command("broadcast") & filters.user(config.OWNER_ID))
async def broadcast_cmd(client, message):
    if len(message.command) < 2:
        await message.reply_text("Usage:\n`/broadcast <your message>`", quote=True)
        return

    text = message.text.split(None, 1)[1]
    sessions = db.get_all_sessions()
    total = len(sessions)
    success = failed = 0

    status = await message.reply_text(f"📢 Starting broadcast to {total} connected userbots...")

    for user_id, session_string in sessions:
        try:
            from telethon import TelegramClient
            from telethon.sessions import StringSession

            tele_client = TelegramClient(StringSession(session_string), config.API_ID, config.API_HASH)
            await tele_client.connect()

            me = await tele_client.get_me()
            await tele_client.send_message(user_id, text)
            print(f"✅ Sent to {me.first_name} ({user_id})")
            success += 1

            await tele_client.disconnect()
        except Exception as e:
            print(f"⚠️ Failed for {user_id}: {e}")
            failed += 1
        await asyncio.sleep(0.4)

    await status.edit_text(f"✅ Broadcast complete!\n\n🟢 Sent: {success}\n🔴 Failed: {failed}")


# -----------------------
# Run the bot
# -----------------------
def run():
    print("🚀 Controller bot started.")
    app.run()