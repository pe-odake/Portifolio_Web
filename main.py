# main.py - Entry point for Flask application
from app import app, db
import routes  # noqa: F401
import os
import logging

# Initialize database and seed data
def initialize_database():
    """Initialize database tables and seed initial data"""
    with app.app_context():
        import models  # noqa: F401
        from models import Category, Tag, About
        
        # Create all tables
        db.create_all()
        logging.info("Database tables created")
        
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
                db.session.add_all(categories)
                logging.info("Categories seeded")
            
            # Seed tags
            if Tag.query.count() == 0:
                tag_names = [
                    'React', 'Python', 'Flask', 'JavaScript', 'Node.js', 
                    'HTML/CSS', 'MongoDB', 'PostgreSQL', 'API', 'Frontend',
                    'Backend', 'Full-Stack', 'Mobile', 'iOS', 'Android',
                    'UI/UX', 'Machine Learning', 'Data Analysis'
                ]
                db.session.add_all([Tag(name=name) for name in tag_names])
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

if __name__ == "__main__":
    # Initialize database on startup
    initialize_database()
    
    # Use debug=False for production
    debug_mode = os.environ.get('DEBUG', 'False').lower() == 'true'
    app.run(host="0.0.0.0", port=5001, debug=debug_mode)