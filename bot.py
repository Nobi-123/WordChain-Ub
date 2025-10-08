# bot.py - Controller bot using Pyrogram (SQLite version) (rewritten & fixed)
import asyncio
import logging
from typing import Optional, List

from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message

from db import DBSessionManager
from userbots.wordchain_player import start_userbot
import config

# Basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("tnc_controller")

# Initialize bot client
app = Client(
    "tnc_controller",
    bot_token=config.BOT_TOKEN,
    api_id=config.API_ID,
    api_hash=config.API_HASH,
)

# Initialize database (synchronous; keep simple wrapper)
db = DBSessionManager(config.DB_PATH)


def mask_session(session: str, keep_chars: int = 6) -> str:
    """
    Return a masked preview of the session token so the raw secret is not leaked.
    Example: "xxxx...ABC123"
    """
    if not session:
        return "N/A"
    session = session.strip()
    if len(session) <= keep_chars:
        return "****"
    return f"****{session[-keep_chars:]}"


def is_maybe_string_session(text: str) -> bool:
    """
    Basic heuristic to accept likely Telethon StringSession values:
    - Not a command (handled above)
    - Minimum length threshold
    - Contains at least some non-space characters
    This intentionally avoids strict regex to be permissive but prevents tiny junk.
    """
    if not text:
        return False
    text = text.strip()
    if len(text) < 40:  # Telethon string sessions are usually longer
        return False
    # Could add more heuristics if needed
    return True


# ------------------------ START COMMAND ------------------------
@app.on_message(filters.command("start") & filters.private)
async def start_cmd(client: Client, message: Message):
    """Send welcome message with owner, channel, and support links."""
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
        # try to send a photo if configured
        if getattr(config, "START_IMAGE", None):
            await message.reply_photo(
                photo=config.START_IMAGE,
                caption=caption,
                reply_markup=buttons,
                parse_mode="HTML",
            )
            return
    except Exception as e:
        logger.warning("Failed to send start photo: %s", e)

    # fallback to text
    await message.reply_text(caption, reply_markup=buttons, parse_mode="HTML")


# ------------------------ CONNECT FLOW ------------------------
@app.on_message(filters.command("connect") & filters.private)
async def connect_cmd(client: Client, message: Message):
    """Prompt the user to send their Telethon string session in private."""
    await message.reply_text(
        "📥 Please send your Telethon <code>StringSession</code> in this private chat.\n\n"
        "⚠️ Never share your session in public groups. This session grants full access to your account.",
        parse_mode="HTML",
    )


@app.on_message(filters.private & filters.text & ~filters.command(["start", "connect", "disconnect", "broadcast", "stats", "listusers"]))
async def receive_session(client: Client, message: Message):
    """
    Receive and store user's StringSession.
    This handler is intentionally permissive to accept multiline sessions but verifies basics.
    """
    text = message.text.strip()
    user = message.from_user
    user_id = user.id

    # Basic filter: ignore messages that look like commands or are too short
    if not is_maybe_string_session(text):
        # Not a plausible session — ignore quietly to avoid revealing heuristics
        logger.debug("Received non-session text from %s (len=%d)", user_id, len(text))
        return

    # Save or update session in DB
    try:
        existing_session = db.get_session(user_id)
        db.save_session(user_id, text)
    except Exception as e:
        logger.exception("DB error when saving session for user %s: %s", user_id, e)
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

    await message.reply_text(user_message, parse_mode="HTML")

    # Start userbot in background
    try:
        # start_userbot is expected to be an async callable that runs the userbot
        asyncio.create_task(start_userbot(text, user_id))
    except Exception as e:
        logger.exception("Failed to start userbot for %s: %s", user_id, e)
        await message.reply_text(
            "⚠️ Failed to start your userbot. The session was saved though. Contact support."
        )

    await message.reply_text("🤖 Your userbot is now active and will join WordChain when ready.")

    # Log connection to admin group — do NOT include raw session. Only include masked preview.
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
        await client.send_message(config.LOG_GROUP_ID, log_text, parse_mode="HTML")
        logger.info("Logged session connect for user %s", user_id)
    except Exception as e:
        # Don't spam errors for logging failures
        logger.warning("Could not send log to group: %s", e)


# ------------------------ DISCONNECT ------------------------
@app.on_message(filters.command("disconnect") & filters.private)
async def disconnect_cmd(client: Client, message: Message):
    """
    Allows a user to disconnect their own session.
    Owner can disconnect any user by `/disconnect <user_id>` (owner-only).
    """
    user = message.from_user
    parts = message.text.split()

    # OWNER disconnects someone else
    if user.id == config.OWNER_ID and len(parts) > 1:
        try:
            target_id = int(parts[1])
        except ValueError:
            await message.reply_text("❌ Invalid user ID format.")
            return

        if db.get_session(target_id):
            db.delete_session(target_id)
            await message.reply_text(
                f"✅ Disconnected user <code>{target_id}</code>.", parse_mode="HTML"
            )
            try:
                await client.send_message(
                    config.LOG_GROUP_ID,
                    f"❌ <b>Userbot Disconnected by Owner</b>\n\nTarget ID: <code>{target_id}</code>",
                    parse_mode="HTML",
                )
            except Exception:
                logger.debug("Could not log owner-initiated disconnect for %s", target_id)
        else:
            await message.reply_text("⚠️ User not found in database.")
        return

    # Regular user disconnects their own userbot
    session = db.get_session(user.id)
    if not session:
        await message.reply_text("⚠️ You don't have an active session.")
        return

    try:
        db.delete_session(user.id)
        await message.reply_text("🛑 Your userbot has been terminated successfully.")
        try:
            await client.send_message(
                config.LOG_GROUP_ID,
                f"🧹 <b>User Disconnected</b>\n\n👤 <b>{user.first_name or 'Unknown'}</b>\n🆔 <code>{user.id}</code>",
                parse_mode="HTML",
            )
        except Exception:
            logger.debug("Could not log user disconnect for %s", user.id)
    except Exception as e:
        logger.exception("Error deleting session for %s: %s", user.id, e)
        await message.reply_text("❌ Failed to disconnect. Please try again later.")


# ------------------------ BROADCAST ------------------------
@app.on_message(filters.command("broadcast") & filters.user(config.OWNER_ID) & filters.private)
async def broadcast_cmd(client: Client, message: Message):
    """
    Owner can broadcast a replied-to message to all connected users.
    Usage: reply to a message with /broadcast
    """
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
            # copy the replied message to the user
            await message.reply_to_message.copy(user_id)
            success += 1
            # tiny sleep to avoid hitting flood limits
            await asyncio.sleep(0.06)
        except Exception as e:
            failed += 1
            logger.debug("Broadcast to %s failed: %s", user_id, e)

    result = f"✅ Broadcast Completed!\n📬 Sent: {success}\n⚠️ Failed: {failed}"
    await message.reply_text(result)

    try:
        await client.send_message(config.LOG_GROUP_ID, f"Broadcast result:\n{result}")
    except Exception:
        logger.debug("Could not log broadcast result.")


# ------------------------ LIST USERS ------------------------
@app.on_message(filters.command("listusers") & filters.user(config.OWNER_ID) & filters.private)
async def list_users_cmd(client: Client, message: Message):
    """List all connected users with IDs (owner-only)."""
    users = db.list_sessions()
    if not users:
        await message.reply_text("📭 No connected users found.")
        return

    lines = ["👥 <b>Connected Users:</b>\n"]
    for index, user_id in enumerate(users, start=1):
        try:
            user_info = await client.get_users(user_id)
            name = user_info.first_name or "Unknown"
            username = f"@{user_info.username}" if user_info.username else "N/A"
            lines.append(f"{index}. {name} ({username}) — <code>{user_id}</code>")
        except Exception:
            lines.append(f"{index}. ❓ Unknown — <code>{user_id}</code>")

    text = "\n".join(lines)
    # Split long lists to avoid message length limits
    for chunk in [text[i:i + 4000] for i in range(0, len(text), 4000)]:
        await message.reply_text(chunk, parse_mode="HTML")


# ------------------------ STATS ------------------------
@app.on_message(filters.command("stats") & filters.user(config.OWNER_ID) & filters.private)
async def stats_cmd(client: Client, message: Message):
    """Display usage stats (owner-only)."""
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

    await message.reply_text(text, parse_mode="HTML")


# ------------------------ RUN APP ------------------------
def run():
    logger.info("🚀 Starting TNC WordChain Controller Bot...")
    app.run()
    logger.info("✅ Bot stopped.")


if __name__ == "__main__":
    run()