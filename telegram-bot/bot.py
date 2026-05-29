import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from pyrogram import Client, idle
from config import BOT_TOKEN, MONGODB_URI, OWNER_ID
import db
from handlers import user as user_handler
from handlers import owner as owner_handler


async def main():
    if not BOT_TOKEN:
        print("ERROR: BOT_TOKEN is not set", flush=True)
        return
    if not MONGODB_URI:
        print("ERROR: MONGODB_URI is not set", flush=True)
        return
    if not OWNER_ID:
        print("ERROR: OWNER_ID is not set", flush=True)
        return

    print(f"Connecting to MongoDB...", flush=True)
    await db.init_db()
    print("MongoDB connected.", flush=True)

    app = Client(
        "smsbot_session",
        bot_token=BOT_TOKEN,
        in_memory=True,
    )

    user_handler.register(app)
    owner_handler.register(app)

    print("Starting bot...", flush=True)
    await app.start()
    me = await app.get_me()
    print(f"Bot started: @{me.username} ({me.id})", flush=True)
    print(f"Owner ID: {OWNER_ID}", flush=True)

    await idle()
    await app.stop()
    print("Bot stopped.", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
