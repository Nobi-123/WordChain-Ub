# userbots/wordchain_player.py — Smart WordChain Auto Player
import asyncio
import random
import re
from telethon import TelegramClient, events
from telethon.sessions import StringSession
import config


# --------------------------
# Load word dictionary
# --------------------------
def import_words(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return [w.strip().lower() for w in f if w.strip()]
    except FileNotFoundError:
        print("❌ words.txt not found!")
        return []


# --------------------------
# Pick valid word
# --------------------------
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


# --------------------------
# Start the game logic
# --------------------------
async def start_game_logic(client, words):
    delay = 2.5
    banned_letters = []
    min_length = 3

    me = await client.get_me()
    my_variants = {me.first_name.lower()}
    if me.last_name:
        my_variants.add(f"{me.first_name.lower()} {me.last_name.lower()}")
    if me.username:
        my_variants.add(me.username.lower())
    my_variants.add(str(me.id))

    print(f"🧩 Listening for turns belonging to: {', '.join(my_variants)}")

    @client.on(events.NewMessage)
    async def on_message(event):
        text = (event.raw_text or "").lower()
        if not text:
            return

        # 1️⃣ Only act when it's OUR turn
        if "turn" in text:
            if not any(name in text for name in my_variants):
                return  # skip others' turns
        else:
            return  # ignore unrelated messages

        # 2️⃣ Detect banned letters
        if "banned letters" in text:
            letters = re.findall(r"[a-z]", text.split("banned letters:")[-1])
            banned_letters[:] = letters
            print(f"🚫 Banned letters: {banned_letters}")

        # 3️⃣ Detect minimum length
        m = re.search(r"at least (\d+) letters", text)
        if m:
            min_length = int(m.group(1))
            print(f"🔤 Minimum length: {min_length}")

        # 4️⃣ Detect required letter
        include_match = re.search(r"include[^a-z]*([a-z])", text)
        include = include_match.group(1) if include_match else ""

        # 5️⃣ Detect starting letter
        prefix_match = re.search(r"start[^a-z]*with[^a-z]*([a-z])", text)
        if prefix_match:
            prefix = prefix_match.group(1)
            word = get_word(words, prefix, include, banned_letters, min_length)
            if word:
                await asyncio.sleep(delay)
                await client.send_message(event.chat_id, word)
                print(f"💬 Sent word: {word}")
            else:
                print(f"⚠️ No valid word found for start='{prefix}', include='{include}'")


# --------------------------
# Start userbot instance
# --------------------------
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