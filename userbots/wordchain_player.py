# userbots/wordchain_player.py - Telethon userbot logic (simplified)
import asyncio, random, re, string, os
from telethon import TelegramClient, events
from telethon.sessions import StringSession
import config

def import_words(path):
    words = []
    try:
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                w = line.strip()
                if w:
                    words.append(w.lower())
    except FileNotFoundError:
        pass
    return words

async def play_loop(client, words_path, user_id):
    dictionary = import_words(words_path)
    # minimal handler for messages in groups
    @client.on(events.NewMessage)
    async def handler(event):
        # basic logic: if it's our turn, send a random word
        txt = event.raw_text or ''
        if 'Your word must start with' in txt or 'Turn:' in txt:
            # choose a random word and send
            if dictionary:
                await asyncio.sleep(2.5)
                await client.send_message(event.chat_id, random.choice(dictionary))
    # run until disconnected
    await client.run_until_disconnected()

async def start_userbot(string_session, user_id):
    client = TelegramClient(StringSession(string_session), config.API_ID, config.API_HASH)
    await client.start()
    await play_loop(client, config.WORDS_PATH, user_id)
