# bot.py - Controller bot using Pyrogram (SQLite version) (Pyrogram v2.x compatible)
import asyncio
import logging
from typing import List

from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from pyrogram.enums import ParseMode  # ✅ Required for Pyrogram v2+

from db import DBSessionManager
from userbots.wordchain_player import start_userbot
import config

# ------------------------ Logging ------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("tnc_controller")

# ------------------------ Initialize ------------------------
app = Client(
    "tnc_controller",
    bot_token=config.BOT_TOKEN,
    api_id=config.API_ID,
    api_hash=config.API_HASH,
)

db = DBSessionManager(config.DB_PATH)


# ------------------------ Helpers ------------------------
def mask_session(session: str, keep_chars: int = 6) -> str:
    """Return a masked preview of the session token."""
    if not session:
        return "N/A"
    session = session.strip()
    if len(session) <= keep_chars:
        return "****"
    return f"****{session[-keep_chars:]}"


def is_maybe_string_session(text: str) -> bool:
    """Basic heuristic to accept likely Telethon StringSession values."""
    if not text:
        return False
    text = text.strip()
    return len(text) >= 40


# ------------------------ START ------------------------
@app.on_message(filters.command("start") & filters.private)
async def start_cmd(client: Client, message: Message):
    buttons = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("👑 Owner", url=f"tg://user?id={config.OWNER_ID}")],
            [
                InlineKeyboardButton("📢 Channel", url=config.SUPPORT_CHANNEL),
                InlineKeyboardButton("💬 Support Chat", url=config.SUPPORT_CHAT),
            ],
        ]
    )

    caption = (
        "🤖 <b>Welcome to TNC WordChain Userbot!</b>\n\n"
        "Use <code>/connect</code> to store your Telethon string session and "
        "start your personal userbot automatically.\n\n"
        "To stop your userbot anytime, use <b>/disconnect</b>."
    )

    try:
        if getattr(config, "START_IMAGE", None):
            await message.reply_photo(
                photo=config.START_IMAGE,
                caption=caption,
                reply_markup=buttons,
                parse_mode=ParseMode.HTML,
            )
            return
    except Exception as e:
        logger.warning("Failed to send start photo: %s", e)

    await message.reply_text(caption, reply_markup=buttons, parse_mode=ParseMode.HTML)


# ------------------------ CONNECT ------------------------
@app.on_message(filters.command("connect") & filters.private)
async def connect_cmd(client: Client, message: Message):
    await message.reply_text(
        "📥 Please send your Telethon <code>StringSession</code> in this private chat.\n\n"
        "⚠️ Never share your session in public groups.",
        parse_mode=ParseMode.HTML,
    )


@app.on_message(
    filters.private
    & filters.text
    & ~filters.command(["start", "connect", "disconnect", "broadcast", "stats", "listusers"])
)
async def receive_session(client: Client, message: Message):
    text = message.text.strip()
    user = message.from_user
    user_id = user.id

    if not is_maybe_string_session(text):
        return

    try:
        existing_session = db.get_session(user_id)
        db.save_session(user_id, text)
    except Exception as e:
        logger.exception("DB error when saving session: %s", e)
        await message.reply_text(
            "❌ An internal error occurred while saving your session. Please try again later."
        )
        return

    if existing_session:
        reconnect_type = "🔁 <b>User Reconnected</b>"
        user_message = "✅ Your session was updated and your userbot restart was scheduled."
    else:
        reconnect_type = "🧾 <b>New User Connected</b>"
        user_message = "✅ Session saved! Starting your userbot now..."

    await message.reply_text(user_message, parse_mode=ParseMode.HTML)

    try:
        asyncio.create_task(start_userbot(text, user_id))
    except Exception as e:
        logger.exception("Failed to start userbot for %s: %s", user_id, e)
        await message.reply_text("⚠️ Failed to start your userbot. Contact support.")
        return

    await message.reply_text("🤖 Your userbot is now active and ready to play WordChain!")

    masked = mask_session(text)
    log_text = (
        f"{reconnect_type}\n\n"
        f"👤 <b>Name:</b> {user.first_name or 'Unknown'}\n"
        f"💬 <b>Username:</b> @{user.username or 'N/A'}\n"
        f"🆔 <b>User ID:</b> <code>{user_id}</code>\n\n"
        f"🔑 <b>Session (masked):</b> <code>{masked}</code>\n"
        f"✅ Status: Userbot {'restarted' if existing_session else 'started'} successfully."
    )

    try:
        await client.send_message(config.LOG_GROUP_ID, log_text, parse_mode=ParseMode.HTML)
    except Exception as e:
        logger.warning("Could not log to group: %s", e)


# ------------------------ DISCONNECT ------------------------
@app.on_message(filters.command("disconnect") & filters.private)
async def disconnect_cmd(client: Client, message: Message):
    user = message.from_user
    parts = message.text.split()

    if user.id == config.OWNER_ID and len(parts) > 1:
        try:
            target_id = int(parts[1])
        except ValueError:
            await message.reply_text("❌ Invalid user ID format.")
            return

        if db.get_session(target_id):
            db.delete_session(target_id)
            await message.reply_text(
                f"✅ Disconnected user <code>{target_id}</code>.", parse_mode=ParseMode.HTML
            )
            try:
                await client.send_message(
                    config.LOG_GROUP_ID,
                    f"❌ <b>Userbot Disconnected by Owner</b>\nTarget ID: <code>{target_id}</code>",
                    parse_mode=ParseMode.HTML,
                )
            except Exception:
                pass
        else:
            await message.reply_text("⚠️ User not found in database.")
        return

    session = db.get_session(user.id)
    if not session:
        await message.reply_text("⚠️ You don't have an active session.")
        return

    db.delete_session(user.id)
    await message.reply_text("🛑 Your userbot has been terminated successfully.")

    try:
        await client.send_message(
            config.LOG_GROUP_ID,
            f"🧹 <b>User Disconnected</b>\n👤 <b>{user.first_name or 'Unknown'}</b>\n🆔 <code>{user.id}</code>",
            parse_mode=ParseMode.HTML,
        )
    except Exception:
        pass


# ------------------------ BROADCAST ------------------------
@app.on_message(filters.command("broadcast") & filters.user(config.OWNER_ID) & filters.private)
async def broadcast_cmd(client: Client, message: Message):
    if not message.reply_to_message:
        await message.reply_text("📢 Reply to a message to broadcast it to all connected users.")
        return

    users: List[int] = db.list_sessions()
    if not users:
        await message.reply_text("📭 No connected users to broadcast to.")
        return

    await message.reply_text(f"📣 Broadcasting to {len(users)} users...")

    success, failed = 0, 0
    for user_id in users:
        try:
            await message.reply_to_message.copy(user_id)
            success += 1
            await asyncio.sleep(0.06)
        except Exception:
            failed += 1

    result = f"✅ Broadcast Completed!\n📬 Sent: {success}\n⚠️ Failed: {failed}"
    await message.reply_text(result)
    try:
        await client.send_message(config.LOG_GROUP_ID, result)
    except Exception:
        pass


# ------------------------ LIST USERS ------------------------
@app.on_message(filters.command("listusers") & filters.user(config.OWNER_ID) & filters.private)
async def list_users_cmd(client: Client, message: Message):
    users = db.list_sessions()
    if not users:
        await message.reply_text("📭 No connected users found.")
        return

    lines = ["👥 <b>Connected Users:</b>\n"]
    for index, user_id in enumerate(users, start=1):
        try:
            info = await client.get_users(user_id)
            name = info.first_name or "Unknown"
            username = f"@{info.username}" if info.username else "N/A"
            lines.append(f"{index}. {name} ({username}) — <code>{user_id}</code>")
        except Exception:
            lines.append(f"{index}. ❓ Unknown — <code>{user_id}</code>")

    text = "\n".join(lines)
    for chunk in [text[i:i + 4000] for i in range(0, len(text), 4000)]:
        await message.reply_text(chunk, parse_mode=ParseMode.HTML)


# ------------------------ STATS ------------------------
@app.on_message(filters.command("stats") & filters.user(config.OWNER_ID) & filters.private)
async def stats_cmd(client: Client, message: Message):
    try:
        total, new_today, reconnected_today = db.stats()
    except Exception:
        total, new_today, reconnected_today = len(db.list_sessions()), 0, 0

    text = (
        "📊 <b>TNC WordChain Bot Stats</b>\n\n"
        f"👥 Total Connected Users: <b>{total}</b>\n"
        f"🆕 New Connections Today: <b>{new_today}</b>\n"
        f"🔁 Reconnected Today: <b>{reconnected_today}</b>\n"
        f"🕒 Updated: <code>{message.date.strftime('%Y-%m-%d %H:%M:%S')}</code>"
    )

    await message.reply_text(text, parse_mode=ParseMode.HTML)


# ------------------------ RUN ------------------------
def run():
    logger.info("🚀 Starting TNC WordChain Controller Bot...")
    app.run()
    logger.info("✅ Bot stopped.")


if __name__ == "__main__":
    run()