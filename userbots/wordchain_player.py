# ==========================================================
# userbots/wordchain_player.py — WordChain Player (Telethon)
# ==========================================================

import asyncio
import random
import re
import logging
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from pyrogram import Client as PyroClient
from pyrogram.enums import ParseMode
import config
from db import DBSessionManager

# Database instance
db = DBSessionManager(config.DB_PATH)

# ----------------------------------------------------------
# Logging setup
# ----------------------------------------------------------
log = logging.getLogger("wordchain_player")
log.setLevel(logging.INFO)


# ----------------------------------------------------------
# Load dictionary safely
# ----------------------------------------------------------
def import_words(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return [w.strip().lower() for w in f if w.strip()]
    except FileNotFoundError:
        log.error("❌ words.txt not found!")
        return []


# ----------------------------------------------------------
# Get a valid word
# ----------------------------------------------------------
def get_word(dictionary, prefix, include="", banned=None, min_len=3):
    banned = banned or []
    valid = [
        w for w in dictionary
        if w.startswith(prefix)
        and (not include or include in w)
        and all(bl not in w for bl in banned)
        and len(w) >= min_len
    ]
    return random.choice(valid) if valid else None


# ----------------------------------------------------------
# Game logic handler
# ----------------------------------------------------------
async def start_game_logic(client, words):
    delay = 2.5
    banned_letters = []
    min_length = 3
    skip_cooldown = False
    current_round = 0

    me = await client.get_me()
    my_id = me.id
    my_name = (me.first_name + (f" {me.last_name}" if me.last_name else "")).strip().lower()
    log.info(f"🎮 Playing as {my_name} ({my_id})")

    # --- Detect turn ownership ---
    def is_my_turn(text: str) -> bool:
        match = re.search(r"turn:\s*([^\n]+)", text, re.IGNORECASE)
        if not match:
            return False
        current_turn = re.sub(r"[^a-zA-Z0-9 ]", "", match.group(1)).strip().lower()
        clean_name = re.sub(r"[^a-zA-Z0-9 ]", "", my_name).strip().lower()
        return clean_name in current_turn or str(my_id) in current_turn

    # --- Monitor messages ---
    target_chat = getattr(config, "WORDCHAIN_GROUP", None)
    if not target_chat:
        log.warning("⚠️ WORDCHAIN_GROUP not set — listening to all chats (debug mode).")

    @client.on(events.NewMessage(chats=target_chat))
    async def on_message(event):
        nonlocal banned_letters, min_length, skip_cooldown, current_round

        text = event.raw_text or ""
        if not text:
            return

        # New round
        if re.search(r"(won the game|new round|starting a new game)", text, re.IGNORECASE):
            banned_letters.clear()
            skip_cooldown = False
            current_round += 1
            log.info(f"🔁 New round started (#{current_round})")
            return

        # AFK / skipped
        if re.search(r"(skipped due to afk|no word given)", text, re.IGNORECASE):
            skip_cooldown = True
            log.info("⏸️ AFK skip detected — pausing 5s")
            await asyncio.sleep(5)
            skip_cooldown = False
            return

        if skip_cooldown or not is_my_turn(text):
            return

        log.info("🟢 It's my turn!")

        # Detect banned letters
        if "banned letters" in text.lower():
            bl = re.findall(r"[A-Za-z]", text.split("Banned letters:")[-1])
            banned_letters[:] = [b.lower() for b in bl]
            log.info(f"🚫 Banned letters: {banned_letters}")

        # Detect minimum length
        m = re.search(r"at least\s*(\d+)\s*letters", text, re.IGNORECASE)
        if m:
            min_length = int(m.group(1))
            log.info(f"🔤 Min length set to {min_length}")

        # Include letter
        include_match = re.search(r"include[^A-Za-z]*([A-Za-z])", text, re.IGNORECASE)
        include = include_match.group(1).lower() if include_match else ""

        # Starting prefix
        prefix_match = re.search(r"start[^A-Za-z]*with[^A-Za-z]*([A-Za-z])", text, re.IGNORECASE)
        if not prefix_match:
            return

        prefix = prefix_match.group(1).lower()
        word = get_word(words, prefix, include, banned_letters, min_length)

        if word:
            await asyncio.sleep(random.uniform(1.8, 3.2))
            try:
                await client.send_message(event.chat_id, word)
                log.info(f"💬 Sent word: {word}")
            except Exception as e:
                log.warning(f"⚠️ Failed to send word: {e}")
        else:
            log.warning(f"⚠️ No valid word found for '{prefix}' (include '{include}')")


# ----------------------------------------------------------
# Main async start
# ----------------------------------------------------------
async def _start_userbot(session_string, user_id):
    client = TelegramClient(StringSession(session_string), config.API_ID, config.API_HASH)

    try:
        await client.start()
        me = await client.get_me()
        log.info(f"✅ Userbot started for {me.first_name} ({me.id})")

        # Load words
        words = import_words(config.WORDS_PATH)
        if not words:
            log.error("⚠️ Empty dictionary — stopping bot.")
            await client.disconnect()
            return

        # Start WordChain logic
        await start_game_logic(client, words)

        # Run until disconnected
        await client.run_until_disconnected()

    except Exception as e:
        log.error(f"❌ Error in userbot for {user_id}: {e}")

    finally:
        # --- Auto cleanup ---
        try:
            db.delete_session(user_id)
            log.info(f"🧹 Session removed for {user_id}")

            # Notify admin via Pyrogram
            bot = PyroClient(
                "cleanup_notifier",
                bot_token=config.BOT_TOKEN,
                api_id=config.API_ID,
                api_hash=config.API_HASH,
            )
            await bot.start()
            await bot.send_message(
                config.LOG_GROUP_ID,
                f"🧾 <b>User Disconnected Automatically</b>\n🆔 <code>{user_id}</code>",
                parse_mode=ParseMode.HTML,
            )
            await bot.stop()
        except Exception as e:
            log.warning(f"⚠️ Cleanup failed for {user_id}: {e}")

        await client.disconnect()
        log.info(f"🛑 Userbot stopped for {user_id}")


# ----------------------------------------------------------
# Entry wrapper (called from bot.py thread)
# ----------------------------------------------------------
def start_userbot(session_string, user_id):
    """Thread-safe entry point"""
    try:
        asyncio.run(_start_userbot(session_string, user_id))
    except RuntimeError:
        # Handles case when already inside running loop (rare)
        loop = asyncio.get_event_loop()
        loop.create_task(_start_userbot(session_string, user_id))