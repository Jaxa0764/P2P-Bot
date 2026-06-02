import hmac
import hashlib
import urllib.parse
import json
import os
from . import config

def verify_telegram_data(init_data: str, bot_token: str) -> dict:
    """
    Verifies the signature of the data received from the Telegram Mini App.
    See: https://core.telegram.org/bots/webapps#validating-data-received-via-the-mini-app
    
    Returns:
        dict: Parsed user object from the init_data query string.
    Raises:
        ValueError: If validation fails or data is invalid.
    """
    if not init_data:
        raise ValueError("initData is empty")
        
    try:
        # Parse query parameters into a dictionary
        parsed_params = dict(urllib.parse.parse_qsl(init_data))
        if "hash" not in parsed_params:
            raise ValueError("No hash parameter found in initData")
            
        received_hash = parsed_params.pop("hash")
        
        # Construct the data check string
        # Elements must be sorted alphabetically by key and joined by newline
        sorted_keys = sorted(parsed_params.keys())
        data_check_string = "\n".join([f"{k}={parsed_params[k]}" for k in sorted_keys])
        
        # Secret key is HMAC-SHA256 signature of the bot token using "WebApps" constant string as key
        secret_key = hmac.new(b"WebApps", bot_token.encode(), hashlib.sha256).digest()
        
        # The validation hash is HMAC-SHA256 signature of data check string using secret key
        calculated_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
        
        if calculated_hash != received_hash:
            raise ValueError("Signature mismatch. Data may have been tampered with.")
            
        # Parse and return user object
        user_json_str = parsed_params.get("user")
        if not user_json_str:
            raise ValueError("User profile not found in initData parameters")
            
        return json.loads(user_json_str)
        
    except Exception as e:
        raise ValueError(f"Telegram initData verification failed: {e}")

def verify_or_mock_telegram_data(init_data: str, bot_token: str) -> dict:
    """
    Verifies Telegram WebApp data or returns a mock user if running in development mode.
    """
    dev_mode = os.getenv("DEV_MODE", "true").lower() == "true"
    
    if not init_data and dev_mode:
        print("[Security] WARNING: Running in DEV MODE. Bypassing Telegram validation with mock user.")
        return {
            "id": 123456789,
            "first_name": "Demo",
            "last_name": "Trader",
            "username": "demo_p2p_trader",
            "language_code": "en"
        }
        
    return verify_telegram_data(init_data, bot_token)
