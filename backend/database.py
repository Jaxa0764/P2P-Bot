import os
import sqlite3
import datetime
from . import config

# Try to initialize Firebase
firebase_initialized = False
db_client = None

if os.path.exists(config.FIREBASE_KEY_PATH):
    try:
        import firebase_admin
        from firebase_admin import credentials
        from firebase_admin import firestore

        cred = credentials.Certificate(config.FIREBASE_KEY_PATH)
        # Check if already initialized to avoid duplicate initialization errors
        if not firebase_admin._apps:
            firebase_admin.initialize_app(cred)
        db_client = firestore.client()
        firebase_initialized = True
        print("[DB] Firebase Firestore initialized successfully.")
    except Exception as e:
        print(f"[DB] Failed to initialize Firebase Firestore: {e}. Falling back to SQLite.")
else:
    print(f"[DB] Firebase key not found at {config.FIREBASE_KEY_PATH}. Using SQLite local fallback.")

# SQLite Fallback configuration
SQLITE_DB_PATH = "p2p_exchange.db"

def init_sqlite():
    """Initializes local SQLite database and creates tables if they do not exist."""
    conn = sqlite3.connect(SQLITE_DB_PATH)
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            telegram_id INTEGER PRIMARY KEY,
            first_name TEXT,
            last_name TEXT,
            username TEXT,
            wallet_address TEXT,
            last_updated TEXT
        )
    """)
    
    # Create transactions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER,
            full_name TEXT,
            username TEXT,
            wallet_address TEXT,
            crypto_type TEXT,
            amount REAL,
            transaction_hash TEXT,
            proof_image_path TEXT,
            timestamp TEXT
        )
    """)
    
    conn.commit()
    conn.close()

if not firebase_initialized:
    init_sqlite()

def save_user(telegram_id, first_name, last_name, username, wallet_address=None):
    """Saves or updates user information in the database."""
    now_str = datetime.datetime.utcnow().isoformat()
    
    if firebase_initialized:
        try:
            user_ref = db_client.collection("users").document(str(telegram_id))
            user_data = {
                "telegram_id": int(telegram_id),
                "first_name": first_name,
                "last_name": last_name,
                "username": username,
                "last_updated": now_str
            }
            if wallet_address:
                user_data["wallet_address"] = wallet_address
                
            user_ref.set(user_data, merge=True)
            print(f"[DB-Firebase] Saved/Updated user {telegram_id}")
            return True
        except Exception as e:
            print(f"[DB-Firebase] Error saving user: {e}")
            # fall through or return False
    
    # SQLite fallback
    try:
        conn = sqlite3.connect(SQLITE_DB_PATH)
        cursor = conn.cursor()
        
        # Check if user exists
        cursor.execute("SELECT wallet_address FROM users WHERE telegram_id = ?", (telegram_id,))
        row = cursor.fetchone()
        
        if row:
            # Update user. Keep existing wallet address if none is provided in current request
            final_wallet = wallet_address if wallet_address else row[0]
            cursor.execute("""
                UPDATE users 
                SET first_name = ?, last_name = ?, username = ?, wallet_address = ?, last_updated = ? 
                WHERE telegram_id = ?
            """, (first_name, last_name, username, final_wallet, now_str, telegram_id))
        else:
            # Insert new user
            cursor.execute("""
                INSERT INTO users (telegram_id, first_name, last_name, username, wallet_address, last_updated)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (telegram_id, first_name, last_name, username, wallet_address, now_str))
            
        conn.commit()
        conn.close()
        print(f"[DB-SQLite] Saved/Updated user {telegram_id}")
        return True
    except Exception as e:
        print(f"[DB-SQLite] Error saving user: {e}")
        return False

def save_transaction(telegram_id, full_name, username, wallet_address, crypto_type, amount, transaction_hash, proof_image_path=None):
    """Saves a new P2P cryptocurrency sale transaction."""
    now_str = datetime.datetime.utcnow().isoformat()
    
    transaction_data = {
        "telegram_id": int(telegram_id),
        "full_name": full_name,
        "username": username,
        "wallet_address": wallet_address,
        "crypto_type": crypto_type,
        "amount": float(amount),
        "transaction_hash": transaction_hash,
        "proof_image_path": proof_image_path,
        "timestamp": now_str
    }
    
    # Save to user first
    save_user(telegram_id, full_name.split()[0] if full_name else "", "", username, wallet_address)
    
    if firebase_initialized:
        try:
            # Create a auto-ID document
            doc_ref = db_client.collection("transactions").document()
            doc_ref.set(transaction_data)
            print(f"[DB-Firebase] Saved transaction {doc_ref.id}")
            
            # Update user's last wallet address in transactions path if needed
            return doc_ref.id
        except Exception as e:
            print(f"[DB-Firebase] Error saving transaction: {e}")
            # fall through to SQLite fallback if firebase write fails
            
    # SQLite fallback
    try:
        conn = sqlite3.connect(SQLITE_DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO transactions (telegram_id, full_name, username, wallet_address, crypto_type, amount, transaction_hash, proof_image_path, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            int(telegram_id), full_name, username, wallet_address, crypto_type, float(amount), transaction_hash, proof_image_path, now_str
        ))
        row_id = cursor.lastrowid
        conn.commit()
        conn.close()
        print(f"[DB-SQLite] Saved transaction with row ID: {row_id}")
        return str(row_id)
    except Exception as e:
        print(f"[DB-SQLite] Error saving transaction: {e}")
        return None

def get_user_transactions(telegram_id):
    """Fetches transaction history for a specific Telegram User ID."""
    if firebase_initialized:
        try:
            docs = db_client.collection("transactions").where("telegram_id", "==", int(telegram_id)).order_by("timestamp", direction="DESCENDING").stream()
            results = []
            for doc in docs:
                data = doc.to_dict()
                data["id"] = doc.id
                results.append(data)
            return results
        except Exception as e:
            print(f"[DB-Firebase] Error fetching transactions: {e}")
            # fall through to SQLite
            
    # SQLite fallback
    try:
        conn = sqlite3.connect(SQLITE_DB_PATH)
        # Use row factory to return dicts instead of tuples
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM transactions 
            WHERE telegram_id = ? 
            ORDER BY timestamp DESC
        """, (int(telegram_id),))
        rows = cursor.fetchall()
        results = [dict(row) for row in rows]
        conn.close()
        return results
    except Exception as e:
        print(f"[DB-SQLite] Error fetching transactions: {e}")
        return []
