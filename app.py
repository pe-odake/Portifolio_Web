# app.py
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
import os
from werkzeug.middleware.proxy_fix import ProxyFix
import logging

# Configure logging
log_level = logging.INFO if not os.environ.get('DEBUG', 'False').lower() == 'true' else logging.DEBUG
logging.basicConfig(level=log_level)

class Base(DeclarativeBase):
    pass

# Initialize Flask app
app = Flask(__name__)

# Ensure SESSION_SECRET is set for security
if not os.environ.get("SESSION_SECRET"):
    raise SystemExit("SESSION_SECRET environment variable must be set for secure sessions")

app.secret_key = os.environ.get("SESSION_SECRET")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)  # needed for url_for to generate with https

# Security configurations
# For local development, allow insecure cookies
app.config['SESSION_COOKIE_SECURE'] = os.environ.get("FLASK_ENV") == "production"  # HTTPS only in production
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_HTTPONLY'] = True

# CSRF Protection
from flask_wtf.csrf import CSRFProtect
csrf = CSRFProtect(app)

# Database configuration: fallback to SQLite if DATABASE_URL not set
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///site.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    'pool_pre_ping': True,
    "pool_recycle": 300,
}

db = SQLAlchemy(app)

# Upload configuration
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'static/uploads')
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['ALLOWED_EXTENSIONS'] = ALLOWED_EXTENSIONS
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Initialize database and seed data only when explicitly called
def init_database():
    """Initialize database tables and seed initial data"""
    pass  # This will be handled by main.py startup
