# bot.py - Controller bot using Pyrogram
import asyncio
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from db import DBSessionManager
from userbots.wordchain_player import start_userbot
import config

app = Client(
    "tnc_controller",
    bot_token=config.BOT_TOKEN,
    api_id=config.API_ID,
    api_hash=config.API_HASH,
)

db = DBSessionManager(config.DB_PATH)


# ------------------------ START COMMAND ------------------------
@app.on_message(filters.command("start") & filters.private)
async def start_cmd(client, message):
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
        "start a personal userbot that plays automatically.\n\n"
        "To stop your userbot anytime, use <b>/disconnect</b>."
    )

    try:
        await message.reply_photo(
            photo=config.START_IMAGE,
            caption=caption,
            reply_markup=buttons,
            disable_web_page_preview=True,
            parse_mode=None
        )
    except Exception as e:
        await message.reply_text(caption, reply_markup=buttons)
        print(f"⚠️ Failed to send start photo: {e}")


# ------------------------ CONNECT FLOW ------------------------
@app.on_message(filters.command("connect") & filters.private)
async def connect_cmd(client, message):
    await message.reply_text(
        "📥 Send your Telethon string session below.\n\n"
        "Make sure it's a valid <code>StringSession</code> (not empty).",
        parse_mode="html"
    )


@app.on_message(filters.private & filters.text)
async def receive_session(client, message):
    text = message.text.strip()
    if len(text) < 20 or message.text.startswith("/"):
        return  # ignore invalid or command-like text

    user = message.from_user
    user_id = user.id
    existing_session = db.get_session(user_id)

    # Save or update session
    db.save_session(user_id, text)

    if existing_session:
        reconnect_type = "🔁 <b>User Reconnected</b>"
        user_message = "✅ Your session was updated and userbot reconnected."
    else:
        reconnect_type = "🧾 <b>New User Connected</b>"
        user_message = "✅ Session saved! Starting your userbot..."

    await message.reply_text(user_message)
    asyncio.create_task(start_userbot(text, user_id))
    await message.reply_text("🤖 Your userbot is now active and ready to play WordChain!")

    # Log connection
    log_text = (
        f"{reconnect_type}\n\n"
        f"👤 <b>Name:</b> {user.first_name or 'Unknown'}\n"
        f"💬 <b>Username:</b> @{user.username or 'N/A'}\n"
        f"🆔 <b>User ID:</b> <code>{user.id}</code>\n"
        f"✅ Status: Userbot {'restarted' if existing_session else 'started'} successfully."
    )

    try:
        await client.send_message(config.LOG_GROUP_ID, log_text, parse_mode="html")
    except Exception as e:
        print(f"⚠️ Could not send log: {e}")


# ------------------------ DISCONNECT ------------------------
@app.on_message(filters.command("disconnect"))
async def disconnect_cmd(client, message):
    user = message.from_user
    parts = message.text.split()

    # OWNER can disconnect anyone
    if user.id == config.OWNER_ID and len(parts) > 1:
        try:
            target_id = int(parts[1])
            if db.get_session(target_id):
                db.delete_session(target_id)
                await message.reply_text(f"✅ Disconnected user <code>{target_id}</code>.", parse_mode="html")

                # log to group
                try:
                    await client.send_message(
                        config.LOG_GROUP_ID,
                        f"❌ Userbot disconnected by owner for <code>{target_id}</code>.",
                        parse_mode="html"
                    )
                except Exception:
                    pass
            else:
                await message.reply_text("⚠️ User not found in database.")
        except Exception:
            await message.reply_text("❌ Invalid user ID format.")
        return

    # Regular user disconnects their own bot
    session = db.get_session(user.id)
    if not session:
        await message.reply_text("⚠️ You don't have an active session.")
        return

    db.delete_session(user.id)
    await message.reply_text("🛑 Your userbot has been terminated successfully.")

    # Log event
    try:
        await client.send_message(
            config.LOG_GROUP_ID,
            f"🧹 <b>User Disconnected</b>\n\n👤 <b>Name:</b> {user.first_name or 'Unknown'}\n🆔 <code>{user.id}</code>",
            parse_mode="html"
        )
    except Exception:
        pass


# ------------------------ BROADCAST ------------------------
@app.on_message(filters.command("broadcast") & filters.user(config.OWNER_ID))
async def broadcast_cmd(client, message):
    if not message.reply_to_message:
        await message.reply_text("📢 Reply to a message to broadcast it to all connected users.")
        return

    users = db.list_sessions()
    success = failed = 0

    await message.reply_text(f"📣 Broadcasting to {len(users)} users...")

    for user_id in users:
        try:
            await message.reply_to_message.copy(user_id)
            success += 1
        except Exception:
            failed += 1

    result = f"✅ Broadcast completed!\n\n📬 Sent: {success}\n⚠️ Failed: {failed}"
    await message.reply_text(result)

    try:
        await client.send_message(config.LOG_GROUP_ID, result)
    except Exception:
        pass


# ------------------------ LIST USERS ------------------------
@app.on_message(filters.command("listusers") & filters.user(config.OWNER_ID))
async def list_users_cmd(client, message):
    users = db.list_sessions()
    if not users:
        await message.reply_text("📭 No connected users found.")
        return

    text_lines = ["👥 <b>Connected Users:</b>\n"]
    for index, user_id in enumerate(users, start=1):
        try:
            user_info = await client.get_users(user_id)
            name = user_info.first_name or "Unknown"
            username = f"@{user_info.username}" if user_info.username else "N/A"
            text_lines.append(f"{index}. {name} ({username}) — <code>{user_id}</code>")
        except Exception:
            text_lines.append(f"{index}. ❓ Unknown — <code>{user_id}</code>")

    text = "\n".join(text_lines)

    # Handle long lists (split into 4000-char chunks)
    chunks = [text[i:i+4000] for i in range(0, len(text), 4000)]
    for chunk in chunks:
        await message.reply_text(chunk, parse_mode="html")


# ------------------------ STATS COMMAND ------------------------
@app.on_message(filters.command("stats") & filters.user(config.OWNER_ID))
async def stats_cmd(client, message):
    total, new_today, reconnected_today = db.stats()
    text = (
        "📊 <b>TNC WordChain Bot Stats</b>\n\n"
        f"👥 Total Connected Users: <b>{total}</b>\n"
        f"🆕 New Connections Today: <b>{new_today}</b>\n"
        f"🔁 Reconnected Today: <b>{reconnected_today}</b>\n"
        f"🕒 Last Update: <code>{message.date.strftime('%Y-%m-%d %H:%M:%S')}</code>"
    )

    await message.reply_text(text, parse_mode="html")


# ------------------------ RUN APP ------------------------
def run():
    print("🚀 Starting TNC WordChain Controller Bot...")
    app.run()
    print("✅ Bot is now live and running!")