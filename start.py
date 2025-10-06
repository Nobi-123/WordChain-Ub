# start.py - Heroku entrypoint
from bot import app

if __name__ == "__main__":
    print("🚀 Starting TNC-WordChain Userbot controller...")
    app.run()
