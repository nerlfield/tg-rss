from telethon.sync import TelegramClient
from telethon.sessions import StringSession
import os

# Read from env for safety; prompt if missing
api_id = os.environ.get("TELEGRAM_API_ID")
api_hash = os.environ.get("TELEGRAM_API_HASH")

if not api_id or not api_hash:
    print("Set TELEGRAM_API_ID and TELEGRAM_API_HASH in your environment first.")
    print("Example:")
    print("  export TELEGRAM_API_ID=123456")
    print("  export TELEGRAM_API_HASH=abcd1234...")
    raise SystemExit(1)

with TelegramClient(StringSession(), int(api_id), api_hash) as client:
    print("Login completed.")
    print("STRING SESSION (copy this into GitHub Secret TELEGRAM_STRING_SESSION):")
    print(client.session.save())