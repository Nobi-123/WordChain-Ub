# userbots/wordchain_player.py — Smart self-turn detection + AFK skip protection
import asyncio
import random
import re
from telethon import TelegramClient, events
from telethon.sessions import StringSession
import config


# --- Load dictionary ---
def import_words(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return [w.strip().lower() for w in f if w.strip()]
    except FileNotFoundError:
        print("❌ words.txt not found!")
        return []


# --- Pick a word that fits current requirements ---
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
    skip_cooldown = False  # prevents spam during AFK skip
    current_round = 0

    me = await client.get_me()
    my_id = me.id
    my_name = (me.first_name + (f" {me.last_name}" if me.last_name else "")).strip().lower()
    print(f"🎮 Playing as: {my_name} ({my_id})")

    # --- Helper: verify if it's our turn ---
    def is_my_turn(text: str) -> bool:
        match = re.search(r"turn:\s*([^\n]+)", text, re.IGNORECASE)
        if not match:
            return False
        current_turn = re.sub(r"[^a-zA-Z0-9 ]", "", match.group(1)).strip().lower()
        clean_name = re.sub(r"[^a-zA-Z0-9 ]", "", my_name).strip().lower()
        return clean_name in current_turn or str(my_id) in current_turn

    @client.on(events.NewMessage)
    async def on_message(event):
        nonlocal banned_letters, min_length, skip_cooldown, current_round
        text = event.raw_text or ""
        if not text:
            return

        # --- Detect round reset / game end ---
        if "won the game" in text.lower() or "new round" in text.lower():
            banned_letters.clear()
            skip_cooldown = False
            current_round += 1
            print(f"🔁 New round detected! (Round {current_round})")
            return

        # --- Handle AFK skip messages ---
        if "skipped due to afk" in text.lower() or "no word given" in text.lower():
            skip_cooldown = True
            print("⏸️ AFK skip triggered — waiting for next round...")
            await asyncio.sleep(5)
            skip_cooldown = False
            return

        # --- Skip if not my turn or during cooldown ---
        if skip_cooldown or not is_my_turn(text):
            return

        print("🟢 My turn detected!")

        # --- Detect banned letters ---
        if "Banned letters:" in text:
            bl = re.findall(r"[A-Za-z]", text.split("Banned letters:")[-1])
            banned_letters[:] = [b.lower() for b in bl]
            print(f"🚫 Banned letters: {banned_letters}")

        # --- Detect minimum word length ---
        m = re.search(r"at least (\d+) letters", text, re.IGNORECASE)
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
        word = get_word(words, prefix, include, banned_letters, min_length)
        if word:
            await asyncio.sleep(delay)
            await client.send_message(event.chat_id, word)
            print(f"💬 Sent word: {word}")
        else:
            print(f"⚠️ No valid word found for prefix '{prefix}', include '{include}'")


async def _start_userbot(session_string, user_id):
    client = TelegramClient(StringSession(session_string), config.API_ID, config.API_HASH)
    await client.start()
    print(f"✅ Userbot session started for {user_id}")
    words = import_words(config.WORDS_PATH)
    await start_game_logic(client, words)
    await client.run_until_disconnected()


def start_userbot(session_string, user_id):
    loop = asyncio.get_event_loop()
    loop.create_task(_start_userbot(session_string, user_id))