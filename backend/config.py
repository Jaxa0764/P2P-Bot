import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Telegram configurations
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not BOT_TOKEN:
    # If running on Vercel, do not crash the initialization if the token is missing.
    # This allows static assets/pages to be served and lets the developer see the error log or configure it.
    if "VERCEL" in os.environ or os.getenv("VERCEL") == "1":
        print("[Warning] TELEGRAM_BOT_TOKEN is not set in Vercel environment variables. Using hardcoded fallback.")
        BOT_TOKEN = "8530598432:AAF1bbxxRvPz-MsfPvoisBr-rKJVkLTE4nA"
    else:
        raise ValueError("TELEGRAM_BOT_TOKEN is not set in the environment variables.")

# Admin IDs to notify (convert comma-separated string to a list of ints)
admin_ids_str = os.getenv("ADMIN_CHAT_IDS", "")
ADMIN_CHAT_IDS = []
if admin_ids_str:
    for x in admin_ids_str.split(","):
        x = x.strip()
        if x.isdigit():
            ADMIN_CHAT_IDS.append(int(x))
        elif x.startswith("-") and x[1:].isdigit():  # negative IDs for groups/channels
            ADMIN_CHAT_IDS.append(int(x))

# Company Wallet configuration shown to the user in the WebApp
COMPANY_WALLETS = {
    "USDT": os.getenv("COMPANY_WALLET_USDT", "0x71C7656EC7ab88b098defB751B7401B5f6d8976F"),
    "BTC": os.getenv("COMPANY_WALLET_BTC", "bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh"),
    "ETH": os.getenv("COMPANY_WALLET_ETH", "0x71C7656EC7ab88b098defB751B7401B5f6d8976F"),
    "TON": os.getenv("COMPANY_WALLET_TON", "EQC6_xP8eB33n7T5Zk9u11tS34fB-y2p7Q_9x8r5k8m1a4eD")
}

# Firebase Configuration
FIREBASE_KEY_PATH = os.getenv("FIREBASE_KEY_PATH", "firebase_key.json")

# Web Server Configuration
PORT = int(os.getenv("PORT", "5000"))
HOST = os.getenv("HOST", "0.0.0.0")
WEBAPP_URL = os.getenv("WEBAPP_URL", "http://localhost:5000")
DEV_MODE = os.getenv("DEV_MODE", "true").lower() == "true"

