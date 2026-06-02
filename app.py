import threading
import sys
import os
from backend.bot import start_bot_polling
from backend.web_server import run_server, app

# Expose the Flask application instance for Vercel and other WSGI/ASGI servers
# Vercel looks for a top-level variable named 'app' in app.py by default.
expose_app_for_vercel = app


if __name__ == "__main__":
    print("==================================================================")
    print("      Starting P2P Crypto Exchange Bot & Web Server Services      ")
    print("==================================================================")
    
    # Enable DEV_MODE by default if not set, to allow easy web browser testing
    if "DEV_MODE" not in os.environ:
        os.environ["DEV_MODE"] = "true"
        print("[System] DEV_MODE not set. Defaulting to 'true' for browser testing.")

    # Start the Telegram Bot polling loop in a background daemon thread.
    # A daemon thread automatically terminates when the main thread (Flask) stops.
    bot_thread = threading.Thread(target=start_bot_polling, daemon=True)
    bot_thread.start()
    print("[System] Background Telegram Bot thread initiated.")

    # Start the Flask web server in the main thread
    try:
        run_server()
    except KeyboardInterrupt:
        print("\n[System] Keyboard interrupt received. Shutting down all services...")
        sys.exit(0)
    except Exception as e:
        print(f"\n[System] Fatal error starting web server: {e}")
        sys.exit(1)
