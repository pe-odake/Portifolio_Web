# main.py - Entry point for Flask application
from app import app
import routes  # noqa: F401
import os

if __name__ == "__main__":
    # Use debug=False for production
    debug_mode = os.environ.get('DEBUG', 'False').lower() == 'true'
    app.run(host="0.0.0.0", port=5000, debug=debug_mode)