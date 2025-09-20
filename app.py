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
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1) # needed for url_for to generate with https

# Security configurations
app.config['SESSION_COOKIE_SECURE'] = True  # HTTPS only
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # CSRF protection
app.config['SESSION_COOKIE_HTTPONLY'] = True  # XSS protection

# CSRF Protection
from flask_wtf.csrf import CSRFProtect
csrf = CSRFProtect(app)

# Database configuration
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    'pool_pre_ping': True,
    "pool_recycle": 300,
}

# No need to call db.init_app(app) here, it's already done in the constructor.
db = SQLAlchemy(app)

# Upload configuration
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['ALLOWED_EXTENSIONS'] = ALLOWED_EXTENSIONS
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Initialize database and seed data
def init_database():
    """Initialize database tables and seed initial data"""
    import models  # noqa: F401
    from models import Category, Tag, About
    
    db.create_all()
    logging.info("Database tables created")
    
    # Seed initial data only if tables are empty
    try:
        # Seed categories
        if Category.query.count() == 0:
            categories = [
                Category(name='Web Development', color='#007bff'),
                Category(name='Mobile Apps', color='#28a745'),
                Category(name='Data Science', color='#dc3545'),
                Category(name='Design', color='#fd7e14'),
                Category(name='API Development', color='#6f42c1'),
                Category(name='Machine Learning', color='#17a2b8')
            ]
            for category in categories:
                db.session.add(category)
            logging.info("Categories seeded")
        
        # Seed tags
        if Tag.query.count() == 0:
            tag_names = [
                'React', 'Python', 'Flask', 'JavaScript', 'Node.js', 
                'HTML/CSS', 'MongoDB', 'PostgreSQL', 'API', 'Frontend',
                'Backend', 'Full-Stack', 'Mobile', 'iOS', 'Android',
                'UI/UX', 'Machine Learning', 'Data Analysis'
            ]
            for tag_name in tag_names:
                db.session.add(Tag(name=tag_name))
            logging.info("Tags seeded")
        
        # Seed about page
        if About.query.count() == 0:
            about = About(
                name='Portfolio Owner',
                title='Full-Stack Developer & Designer',
                bio='Passionate developer with expertise in modern web technologies and user experience design. I love creating innovative solutions that make a difference.',
                location='São Paulo, Brasil',
                email='contato@portfolio.dev',
                skills='["Python", "JavaScript", "React", "Flask", "Node.js", "PostgreSQL", "MongoDB", "UI/UX Design", "Git", "Docker"]',
                languages='["Portuguese", "English", "Spanish"]',
                interests='["Web Development", "Open Source", "Technology Innovation", "User Experience", "Music", "Photography"]'
            )
            db.session.add(about)
            logging.info("About page seeded")
        
        db.session.commit()
        logging.info("Initial data seeding completed")
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error seeding initial data: {e}")

# Create tables and seed data
# Need to put this in module-level to make it work with Gunicorn.
with app.app_context():
    init_database()