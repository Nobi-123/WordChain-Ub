# userbots/wordchain_player.py — Auto WordChain Player (Smart Detection)
import asyncio
import random
import re
from telethon import TelegramClient, events
from telethon.sessions import StringSession
import config


def import_words(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return [w.strip().lower() for w in f if w.strip()]
    except FileNotFoundError:
        print("❌ words.txt not found!")
        return []


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
    delay = 2.5
    banned_letters = []
    min_length = 3
    my_name = None

    me = await client.get_me()
    my_name = f"{me.first_name or ''} {me.last_name or ''}".strip().lower()

    print(f"🧩 Listening for turns belonging to: {my_name}")

    @client.on(events.NewMessage)
    async def on_message(event):
        text = (event.raw_text or "").lower()
        if not text:
            return

        # Detect "turn" message and only act on your turn
        if "turn" in text:
            if my_name not in text:
                # Not your turn
                return

        # Detect banned letters
        if "banned letters" in text:
            letters = re.findall(r"[a-z]", text)
            banned_letters[:] = letters
            print(f"🚫 Banned letters: {banned_letters}")

        # Detect minimum length
        m = re.search(r"at least (\d+) letters", text)
        if m:
            min_length = int(m.group(1))
            print(f"🔤 Minimum length: {min_length}")

        # Detect required letter
        include_match = re.search(r"include[^a-z]*([a-z])", text)
        include = include_match.group(1) if include_match else ""

        # Detect starting letter
        prefix_match = re.search(r"start[^a-z]*with[^a-z]*([a-z])", text)
        if prefix_match:
            prefix = prefix_match.group(1)
            word = get_word(words, prefix, include, banned_letters, min_length)
            if word:
                await asyncio.sleep(delay)
                await client.send_message(event.chat_id, word)
                print(f"💬 Sent word: {word}")
            else:
                print(f"⚠️ No valid word for prefix={prefix}, include={include}")


async def _start_userbot(session_string, user_id):
    try:
        client = TelegramClient(StringSession(session_string), config.API_ID, config.API_HASH)
        await client.start()
        print(f"✅ Userbot started for {user_id}")
        words = import_words(config.WORDS_PATH)
        await start_game_logic(client, words)
        await client.run_until_disconnected()
    except Exception as e:
        print(f"❌ Error in userbot for {user_id}: {e}")


def start_userbot(session_string, user_id):
    loop = asyncio.get_event_loop()
    loop.create_task(_start_userbot(session_string, user_id))