# P2P Crypto Exchange Telegram Bot & Mini App

A professional, production-ready P2P Cryptocurrency Exchange platform that allows users to submit sale transaction receipts through a sleek Telegram Mini App, which instantly stores transaction logs in Firebase Firestore (or a local SQLite database fallback) and alerts administrators via the Telegram Bot.

---

## Key Features

* **Sleek WebApp UI**: Premium glassmorphic dark-theme front-end with loading coin animations, responsive layouts, and interactive toast notifications.
* **Mock Wallet Connectivity**: Connects to EVM, Bitcoin, and TON networks with simulated addresses and visual indicator states.
* **Firebase Firestore + SQLite Auto-Fallback**: Write transactions directly to Google Firestore if credentials are provided; falls back automatically to a local SQLite database (`p2p_exchange.db`) for zero-setup developer previews.
* **Secure WebApp Signatures**: Implements Telegram signature verification (`initData` hash check with HMAC-SHA256) to prevent spoofing of user details.
* **Instant Admin Telegram Alerts**: Sends formatted message notifications to all administrators upon transaction receipt.
* **Optional screenshot uploader**: Supports dragging and dropping or selecting transaction proof screenshots, processing them as base64 on-server.

---

## Tech Stack

* **Backend**: Python (Flask, pyTelegramBotAPI, Firebase Admin SDK)
* **Frontend**: HTML5, CSS3 (Vanilla), JavaScript (ES6+), Telegram Web Apps SDK
* **Database**: Firebase Firestore (NoSQL) / SQLite (SQL)

---

## Directory Structure

```
P2P bot/
├── backend/
│   ├── __init__.py
│   ├── bot.py          # Telegram bot handlers & commands
│   ├── config.py       # Configuration parser
│   ├── database.py     # Database wrapper (Firestore + SQLite fallback)
│   ├── security.py     # Telegram signature verification
│   └── web_server.py   # Flask API & static file serving
├── static/
│   ├── index.html      # Mini App main page
│   ├── css/
│   │   └── style.css   # Glassmorphic Dark styling & keyframes
│   └── js/
│       └── app.js      # Telegram SDK, Mock wallet connect, API requests
├── requirements.txt    # Python dependencies
├── .env                # Configured environment variables (ignored by git)
├── .env.example        # Environment variables template
├── app.py              # Unified daemon runner entrypoint
└── README.md           # Documentation
```

---

## Getting Started

### 1. Prerequisites
Ensure you have Python 3.8+ installed on your system.

### 2. Install Dependencies
Run the following command to install the required packages:
```bash
pip install -r requirements.txt
```

### 3. Configure Settings
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Fill out the parameters inside `.env`:
* `TELEGRAM_BOT_TOKEN`: Set to your bot token from [@BotFather](https://t.me/BotFather).
* `ADMIN_CHAT_IDS`: Comma-separated list of Telegram User IDs that should receive alerts (e.g. `987654321,123456789`). You can find your ID using [@userinfobot](https://t.me/userinfobot).
* `WEBAPP_URL`: The HTTPS URL where the Mini App is served (see Ngrok setup below).

### 4. Running the Application
Launch the unified server and bot daemon:
```bash
python app.py
```
This runs the Flask server on `http://localhost:5000` and starts the Telegram Bot polling concurrently.

---

## Setting up Database (Firebase Firestore vs SQLite)

### SQLite Local Fallback (Default)
By default, the application runs in **Developer Mode** (`DEV_MODE=true` in `app.py`) and does not require any database configuration. If the file specified by `FIREBASE_KEY_PATH` (default: `firebase_key.json`) does not exist, the app writes and reads from a local `p2p_exchange.db` SQLite database.

### Firebase Firestore Setup (Production)
To connect the backend to your Google Firebase Firestore:
1. Go to the [Firebase Console](https://console.firebase.google.com/).
2. Create a new Firebase project.
3. Click on the Gear icon next to **Project Overview** -> **Project Settings**.
4. Go to the **Service Accounts** tab.
5. Click **Generate New Private Key**, then download the `.json` file.
6. Rename this file to `firebase_key.json` and place it in the root directory of this project (or update `FIREBASE_KEY_PATH` in `.env`).
7. Restart `app.py`. The database client will automatically detect the key and switch to Firestore.

---

## How to Test in Telegram (Ngrok Setup)

Telegram requires Mini Apps to load from secure, public **HTTPS** URLs. To test this locally, you can use [ngrok](https://ngrok.com/) to tunnel your local Flask server.

1. Download and install ngrok.
2. Start the local server: `python app.py` (running on port `5000`).
3. In a separate terminal, expose port `5000` using ngrok:
   ```bash
   ngrok http 5000
   ```
4. Copy the secure HTTPS URL provided by ngrok (e.g., `https://abcd-12-34.ngrok-free.app`).
5. Open your `.env` file and set `WEBAPP_URL` to this URL:
   ```env
   WEBAPP_URL=https://abcd-12-34.ngrok-free.app
   ```
6. Restart your python app (`app.py`).
7. Update your Mini App URL in [@BotFather](https://t.me/BotFather):
   - Type `/newapp` or edit your existing WebApp.
   - When asked for the URL, paste your HTTPS ngrok URL.
8. Start the bot on Telegram (`/start`) and tap the **💱 P2P Trading** button to launch your app.
