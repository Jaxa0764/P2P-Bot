import os
import uuid
import base64
from flask import Flask, request, jsonify, send_from_directory, send_file
from . import config
from . import database
from . import security
from . import bot

# Initialize Flask app pointing to the static folder
# Note: static folder is in the parent directory relative to this module
template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'static'))
app = Flask(__name__, static_folder=template_dir, static_url_path='')

# Ensure uploads directory exists
UPLOAD_FOLDER = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'uploads'))
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def save_proof_image(base64_data):
    """Decodes a base64 image and saves it to the uploads folder."""
    if not base64_data:
        return None
    try:
        # Check if the image starts with data URI prefix (e.g. data:image/png;base64,)
        header = ""
        if "," in base64_data:
            header, base64_data_clean = base64_data.split(",", 1)
        else:
            base64_data_clean = base64_data
            
        # Determine file extension
        ext = "png"
        if "jpeg" in header or "jpg" in header:
            ext = "jpg"
        elif "webp" in header:
            ext = "webp"
            
        # Decode base64 bytes
        img_data = base64.b64decode(base64_data_clean)
        filename = f"proof_{uuid.uuid4().hex}.{ext}"
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        
        with open(filepath, "wb") as f:
            f.write(img_data)
            
        # Return local path/url reference (relative to server)
        return f"/uploads/{filename}"
    except Exception as e:
        print(f"[Server] Failed to decode and save proof image: {e}")
        return None

@app.route('/')
def serve_index():
    """Serves the main Mini App HTML page."""
    return send_file(os.path.join(app.static_folder, 'index.html'))

@app.route('/uploads/<filename>')
def serve_upload(filename):
    """Serves uploaded proof images."""
    return send_from_directory(UPLOAD_FOLDER, filename)

@app.route('/api/config', methods=['GET'])
def get_public_config():
    """Returns public configuration settings needed by the Mini App."""
    return jsonify({
        "company_wallets": config.COMPANY_WALLETS,
        "dev_mode": config.DEV_MODE
    })

@app.route('/api/submit', methods=['POST'])
def submit_transaction():
    """Verifies user, stores transaction data, and alerts admins."""
    try:
        data = request.json or {}
        init_data = data.get("initData")
        
        # Verify Telegram user
        try:
            tg_user = security.verify_or_mock_telegram_data(init_data, config.BOT_TOKEN)
        except ValueError as err:
            return jsonify({"status": "error", "message": f"Authentication failed: {str(err)}"}), 401
            
        # Form details
        crypto_type = data.get("crypto_type")
        amount = data.get("amount")
        tx_hash = data.get("transaction_hash")
        wallet_address = data.get("wallet_address")  # User's wallet address
        proof_image_b64 = data.get("proof_image")    # Optional base64 proof image
        
        # Validation of required inputs
        if not all([crypto_type, amount, tx_hash, wallet_address]):
            return jsonify({"status": "error", "message": "Missing required fields"}), 400
            
        try:
            amount_float = float(amount)
            if amount_float <= 0:
                raise ValueError()
        except ValueError:
            return jsonify({"status": "error", "message": "Amount must be a positive number"}), 400
            
        # Handle optional proof image upload
        proof_image_path = save_proof_image(proof_image_b64)
        
        # Save to database
        full_name = f"{tg_user.get('first_name', '')} {tg_user.get('last_name', '')}".strip() or "Telegram User"
        username = tg_user.get('username', 'N/A')
        telegram_id = tg_user.get('id')
        
        tx_id = database.save_transaction(
            telegram_id=telegram_id,
            full_name=full_name,
            username=username,
            wallet_address=wallet_address,
            crypto_type=crypto_type,
            amount=amount_float,
            transaction_hash=tx_hash,
            proof_image_path=proof_image_path
        )
        
        if not tx_id:
            return jsonify({"status": "error", "message": "Failed to save transaction to database"}), 500
            
        # Retrieve the saved transaction details to compile accurate timestamps in notification
        history = database.get_user_transactions(telegram_id)
        saved_tx = next((t for t in history if str(t.get('id')) == str(tx_id)), {})
        
        # Send instant notification to admins via the bot
        bot.send_admin_notification(saved_tx)
        
        return jsonify({
            "status": "success",
            "message": "Transaction submitted successfully",
            "transaction": saved_tx
        })
        
    except Exception as e:
        print(f"[Server] Error submitting transaction: {e}")
        return jsonify({"status": "error", "message": "An internal server error occurred"}), 500

@app.route('/api/transactions', methods=['GET'])
def get_transactions():
    """Fetches user transaction history after verification."""
    init_data = request.args.get("initData")
    try:
        tg_user = security.verify_or_mock_telegram_data(init_data, config.BOT_TOKEN)
        telegram_id = tg_user.get("id")
        
        transactions = database.get_user_transactions(telegram_id)
        return jsonify({
            "status": "success",
            "transactions": transactions
        })
    except ValueError as err:
        return jsonify({"status": "error", "message": f"Authentication failed: {str(err)}"}), 401
    except Exception as e:
        print(f"[Server] Error fetching transactions: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

def run_server():
    """Starts the Flask development server."""
    print(f"[Server] Starting Web App Flask server on {config.HOST}:{config.PORT}...")
    # debug=False inside subthread, reloader must be disabled
    app.run(host=config.HOST, port=config.PORT, debug=False, use_reloader=False)
