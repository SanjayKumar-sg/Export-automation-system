"""
run.py — Application entry point for the Export Automation System.

Usage:
    python run.py              # Development server
    gunicorn -w 4 run:app      # Production (Linux)
"""
import os
from dotenv import load_dotenv

# Load environment variables before anything else
load_dotenv()

from app import create_app

app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_ENV", "development") == "development"
    app.run(host="0.0.0.0", port=port, debug=debug, use_reloader=debug)
