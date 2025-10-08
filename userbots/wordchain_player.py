# userbots/wordchain_player.py — balanced turn detection
import asyncio, random, re
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
    banned_letters, min_length = [], 3

    me = await client.get_me()
    my_first = me.first_name.lower()
    my_display = f"{me.first_name} {me.last_name}".lower() if me.last_name else my_first
    print(f"🧩 Watching for turns for: {my_display}")

    @client.on(events.NewMessage)
    async def on_message(event):
        text = event.raw_text or ""
        if not text:
            return

        # Only care about WordChain bot messages
        if "your word must start with" not in text.lower() and "turn" not in text.lower():
            return

        # --- Turn detection ---
        # Is it our turn or are we the next player?
        turn_line = text.lower()
        if "turn:" in turn_line:
            if my_first not in turn_line and my_display not in turn_line and "next:" in turn_line and my_first not in turn_line.split("next:")[-1]:
                return  # not our turn or next, skip

        # --- Parse rules ---
        if "banned letters:" in text:
            banned_letters[:] = re.findall(r"[a-z]", text.split("banned letters:")[-1].lower())
            print(f"🚫 Banned letters: {banned_letters}")

        m = re.search(r"at least (\d+) letters", text, re.IGNORECASE)
        if m:
            min_length = int(m.group(1))
            print(f"🔤 Minimum length: {min_length}")

        include_match = re.search(r"include[^A-Za-z]*([A-Za-z])", text, re.IGNORECASE)
        include = include_match.group(1).lower() if include_match else ""

        prefix_match = re.search(r"start[^A-Za-z]*with[^A-Za-z]*([A-Za-z])", text, re.IGNORECASE)
        if prefix_match:
            prefix = prefix_match.group(1).lower()
            word = get_word(words, prefix, include, banned_letters, min_length)
            if word:
                await asyncio.sleep(delay)
                await client.send_message(event.chat_id, word)
                print(f"💬 Sent: {word}")
            else:
                print(f"⚠️ No valid word for '{prefix}' include='{include}'")

async def _start_userbot(session_string, user_id):
    client = TelegramClient(StringSession(session_string), config.API_ID, config.API_HASH)
    await client.start()
    print(f"✅ Userbot started for {user_id}")
    words = import_words(config.WORDS_PATH)
    await start_game_logic(client, words)
    await client.run_until_disconnected()

def start_userbot(session_string, user_id):
    loop = asyncio.get_event_loop()
    loop.create_task(_start_userbot(session_string, user_id))