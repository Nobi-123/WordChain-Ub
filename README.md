# TNC-WordChain-Userbot

A Heroku-deployable controller bot that lets users connect Telethon string sessions and run personal userbots that auto-play WordChain games using a large dictionary.

## Features
- Controller bot (Pyrogram) with /start and /connect
- Per-user Telethon userbots (string session) that run the wordchain player
- SQLite session storage
- Heroku-ready (Procfile + start.py)

## Files
- `start.py` - Heroku entrypoint
- `bot.py` - Controller bot (Pyrogram)
- `userbots/wordchain_player.py` - simplified userbot logic (Telethon)
- `words.txt` - your word list (included)
- `assets/start_banner.jpg` - start banner image
- `config.py` - environment-configured settings
- `sessions.db` - created at runtime (not included)

## Deploy to Heroku
1. Create a new Heroku app.
2. Set the config vars (see `.env.example`). Important: set `BOT_TOKEN`, `API_ID`, `API_HASH`.
3. Push this repository to Heroku (git) and deploy. Procfile runs `start.py`.

## Local testing
1. Create a virtualenv and install requirements: `pip install -r requirements.txt`
2. Copy `.env.example` to `.env` and fill values.
3. Run `python start.py`

## License
MIT
