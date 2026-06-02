import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
import datetime
from . import config

# Initialize the Bot with the bot token
bot = telebot.TeleBot(config.BOT_TOKEN)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    """Sends the welcome message with the P2P Trading Mini App button."""
    welcome_text = (
        "🎉 WELCOME!\n\n"
        "Thank you for using our P2P Crypto Exchange Service.\n"
        "Sell your cryptocurrency securely and receive your payment after verification.\n"
        "Click the button below to continue."
    )
    
    markup = InlineKeyboardMarkup()
    # Configure the Web App inline button
    # Note: WEBAPP_URL must be a secure HTTPS URL for Telegram to load it in-app.
    web_app_info = WebAppInfo(url=config.WEBAPP_URL)
    btn_p2p = InlineKeyboardButton(text="💱 P2P Trading", web_app=web_app_info)
    markup.add(btn_p2p)
    
    try:
        bot.send_message(message.chat.id, welcome_text, reply_markup=markup)
        print(f"[Bot] Sent welcome message to user {message.from_user.id} ({message.from_user.username})")
    except Exception as e:
        print(f"[Bot] Error sending welcome message: {e}")

def send_admin_notification(tx_data):
    """Sends a notification to all configured administrators about a new transaction."""
    if not config.ADMIN_CHAT_IDS:
        print("[Bot] Warning: No admin IDs configured. Set ADMIN_CHAT_IDS in your .env file.")
        return False
        
    try:
        # Parse timestamp (expecting ISO format string)
        timestamp_str = tx_data.get("timestamp", datetime.datetime.utcnow().isoformat())
        try:
            dt = datetime.datetime.fromisoformat(timestamp_str)
        except Exception:
            dt = datetime.datetime.utcnow()
            
        date_str = dt.strftime("%Y-%m-%d")
        time_str = dt.strftime("%H:%M:%S UTC")
        
        # Format the notification text as requested
        notification_text = (
            "🔔 New Transaction Received\n\n"
            f"👤 Name: {tx_data.get('full_name', 'N/A')}\n"
            f"📧 Username: @{tx_data.get('username', 'N/A')}\n"
            f"🆔 Telegram ID: {tx_data.get('telegram_id', 'N/A')}\n"
            f"💳 Wallet Address: {tx_data.get('wallet_address', 'N/A')}\n"
            f"🪙 Crypto Type: {tx_data.get('crypto_type', 'N/A')}\n"
            f"💰 Amount: {tx_data.get('amount', 'N/A')} {tx_data.get('crypto_type', '')}\n"
            f"🔗 Transaction Hash: {tx_data.get('transaction_hash', 'N/A')}\n"
            f"📅 Date: {date_str}\n"
            f"🕒 Time: {time_str}"
        )
        
        success = True
        for admin_id in config.ADMIN_CHAT_IDS:
            try:
                bot.send_message(admin_id, notification_text)
                print(f"[Bot] Sent admin notification to admin {admin_id}")
            except Exception as e:
                print(f"[Bot] Failed to send notification to admin {admin_id}: {e}")
                success = False
                
        return success
    except Exception as e:
        print(f"[Bot] Error compiling admin notification: {e}")
        return False

def start_bot_polling():
    """Starts the bot in infinite polling mode."""
    print("[Bot] Telegram Bot starting infinity polling...")
    bot.infinity_polling()
