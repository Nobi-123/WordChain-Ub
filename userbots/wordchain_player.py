# userbots/wordchain_player.py — Auto name detection version
import asyncio
import random
import re
from telethon import TelegramClient, events
from telethon.sessions import StringSession
import config

# ---- Load word list ----
def import_words(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return [w.strip().lower() for w in f if w.strip()]
    except FileNotFoundError:
        print("❌ words.txt not found!")
        return []

# ---- Pick a valid word ----
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

# ---- Main logic ----
async def start_game_logic(client, words):
    delay = 2.5
    banned_letters, min_length = [], 3

    me = await client.get_me()
    print(f"🧩 Userbot ready: {me.first_name} ({me.id})")

    @client.on(events.NewMessage)
    async def on_message(event):
        text = event.raw_text or ""
        if not text:
            return

        low = text.lower()

        # Ignore irrelevant messages
        if "turn:" not in low and "your word must" not in low:
            return

        # 🧠 Always fetch the latest Telegram name in case it changed
        me_now = await client.get_me()
        current_names = {
            me_now.first_name.lower(),
            f"{me_now.first_name} {me_now.last_name}".lower() if me_now.last_name else "",
        }

        # --- Turn detection ---
        if "turn:" in low:
            m = re.search(r"turn[:\s]*([A-Za-z0-9_ ]+)", text, re.IGNORECASE)
            if m:
                turn_name = m.group(1).strip().lower()
                if not any(name and name in turn_name for name in current_names):
                    return  # not your turn → skip

        # --- Parse rules ---
        if "banned letters:" in low:
            banned_letters[:] = re.findall(r"[a-z]", low.split("banned letters:")[-1])
            print(f"🚫 Banned letters: {banned_letters}")

        m = re.search(r"at least (\d+) letters", text, re.IGNORECASE)
        if m:
            min_length = int(m.group(1))
            print(f"🔤 Minimum length: {min_length}")

        include_match = re.search(r"include[^A-Za-z]*([A-Za-z])", text, re.IGNORECASE)
        include = include_match.group(1).lower() if include_match else ""

        prefix_match = re.search(r"start[^A-Za-z]*with[^A-Za-z]*([A-Za-z])", text, re.IGNORECASE)
        if not prefix_match:
            return

        prefix = prefix_match.group(1).lower()
        word = get_word(words, prefix, include, banned_letters, min_length)

        if word:
            await asyncio.sleep(random.uniform(2.0, 3.5))
            await client.send_message(event.chat_id, word)
            print(f"💬 [{me_now.first_name}] played: {word}")
        else:
            print(f"⚠️ [{me_now.first_name}] no valid word for '{prefix}' include='{include}'")

# ---- Launch userbot ----
async def _start_userbot(session_string, user_id):
    client = TelegramClient(StringSession(session_string), config.API_ID, config.API_HASH)
    await client.start()
    words = import_words(config.WORDS_PATH)
    await start_game_logic(client, words)
    await client.run_until_disconnected()

def start_userbot(session_string, user_id):
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    loop.create_task(_start_userbot(session_string, user_id))