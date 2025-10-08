# userbots/wordchain_player.py — WordChain Player with self-turn detection & auto cleanup
import asyncio
import random
import re
from telethon import TelegramClient, events
from telethon.sessions import StringSession
import config
from db import DBSessionManager

db = DBSessionManager(config.DB_PATH)


# --- Load words safely ---
def import_words(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return [w.strip().lower() for w in f if w.strip()]
    except FileNotFoundError:
        print("❌ words.txt not found!")
        return []


# --- Pick a valid word ---
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


async def start_game_logic(client, words):
    """Handles WordChain game logic"""
    delay = 2.5
    banned_letters = []
    min_length = 3
    skip_cooldown = False
    current_round = 0

    me = await client.get_me()
    my_id = me.id
    my_name = (me.first_name + (f" {me.last_name}" if me.last_name else "")).strip().lower()
    print(f"🎮 Playing as: {my_name} ({my_id})")

    # --- Helper: Detect turn ownership ---
    def is_my_turn(text: str) -> bool:
        match = re.search(r"turn:\s*([^\n]+)", text, re.IGNORECASE)
        if not match:
            return False
        current_turn = re.sub(r"[^a-zA-Z0-9 ]", "", match.group(1)).strip().lower()
        clean_name = re.sub(r"[^a-zA-Z0-9 ]", "", my_name).strip().lower()
        return clean_name in current_turn or str(my_id) in current_turn

    # --- Listen to messages in WordChain group only ---
    @client.on(events.NewMessage(chats=config.WORDCHAIN_GROUP))
    async def on_message(event):
        nonlocal banned_letters, min_length, skip_cooldown, current_round
        text = event.raw_text or ""
        if not text:
            return

        # --- Round reset / new game ---
        if re.search(r"(won the game|new round|starting a new game)", text, re.IGNORECASE):
            banned_letters.clear()
            skip_cooldown = False
            current_round += 1
            print(f"🔁 New round started (#{current_round})")
            return

        # --- AFK / skip messages ---
        if re.search(r"(skipped due to afk|no word given)", text, re.IGNORECASE):
            skip_cooldown = True
            print("⏸️ AFK skip — pausing 5s")
            await asyncio.sleep(5)
            skip_cooldown = False
            return

        # --- Skip if not our turn or in cooldown ---
        if skip_cooldown or not is_my_turn(text):
            return

        print("🟢 Detected my turn!")

        # --- Detect banned letters ---
        if "banned letters" in text.lower():
            bl = re.findall(r"[A-Za-z]", text.split("Banned letters:")[-1])
            banned_letters[:] = [b.lower() for b in bl]
            print(f"🚫 Banned letters: {banned_letters}")

        # --- Detect minimum word length ---
        m = re.search(r"at least\s*(\d+)\s*letters", text, re.IGNORECASE)
        if m:
            min_length = int(m.group(1))
            print(f"🔤 Minimum length: {min_length}")

        # --- Detect required include letter ---
        include_match = re.search(r"include[^A-Za-z]*([A-Za-z])", text, re.IGNORECASE)
        include = include_match.group(1).lower() if include_match else ""

        # --- Detect starting letter ---
        prefix_match = re.search(r"start[^A-Za-z]*with[^A-Za-z]*([A-Za-z])", text, re.IGNORECASE)
        if not prefix_match:
            return

        prefix = prefix_match.group(1).lower()

        # --- Pick and send word ---
        word = get_word(words, prefix, include, banned_letters, min_length)
        if word:
            await asyncio.sleep(random.uniform(1.8, 3.2))
            try:
                await client.send_message(event.chat_id, word)
                print(f"💬 Sent word: {word}")
            except Exception as e:
                print(f"⚠️ Failed to send: {e}")
        else:
            print(f"⚠️ No valid word found for '{prefix}', include '{include}'")


# --- Start userbot session ---
async def _start_userbot(session_string, user_id):
    client = TelegramClient(StringSession(session_string), config.API_ID, config.API_HASH)
    try:
        await client.start()
        me = await client.get_me()
        print(f"✅ Userbot started for {me.first_name} ({me.id})")

        # Load dictionary and begin
        words = import_words(config.WORDS_PATH)
        await start_game_logic(client, words)

        # Run until disconnected
        await client.run_until_disconnected()

    except Exception as e:
        print(f"❌ Error in userbot for {user_id}: {e}")

    finally:
        # --- Auto cleanup when disconnected ---
        try:
            db.delete_session(user_id)
            print(f"🧹 Session auto-removed for {user_id}")
            from pyrogram import Client
            bot = Client("cleanup_notifier", bot_token=config.BOT_TOKEN, api_id=config.API_ID, api_hash=config.API_HASH)
            await bot.start()
            await bot.send_message(
                config.LOG_GROUP_ID,
                f"🧾 <b>User Disconnected Automatically</b>\n🆔 <code>{user_id}</code>",
                parse_mode="html"
            )
            await bot.stop()
        except Exception as e:
            print(f"⚠️ Cleanup failed for {user_id}: {e}")

        await client.disconnect()
        print(f"🛑 Userbot stopped for {user_id}")


def start_userbot(session_string, user_id):
    asyncio.create_task(_start_userbot(session_string, user_id))