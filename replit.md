# Portfolio Digital Interativo

## Overview
A Flask-based interactive digital portfolio application that allows users to showcase their projects, receive comments, and manage their professional profile. The application includes authentication via Replit Auth, project management, category/tag system, and social features like likes and comments.

## Recent Changes
- **2025-09-20**: Successfully imported from GitHub and configured for Replit environment
  - Installed Python 3.11 and all required dependencies
  - Created PostgreSQL database with all necessary tables
  - Set up SESSION_SECRET environment variable for secure sessions
  - Created uploads directory for file storage
  - **SECURITY FIXES**: Fixed critical authentication vulnerabilities
    - Replaced unverified JWT decoding with secure userinfo endpoint
    - Fixed require_login decorator to work properly with Flask-Dance
    - Ensured proper user session management and OAuth flow
  - **DATA SEEDING**: Implemented automatic initial data seeding
    - Categories, tags, and about page data automatically created
    - First user automatically becomes admin/owner
  - **PRODUCTION READY**: Configured for production deployment
    - Added Gunicorn WSGI server for production
    - Cleaned up requirements.txt dependencies
    - Configured autoscale deployment with proper production settings
    - Added all necessary error templates (403, 404, 500)
  - Application running successfully on port 5000

## Project Architecture

### Backend (Flask)
- **Framework**: Flask 2.3.3 with SQLAlchemy 3.0.5
- **Database**: PostgreSQL (Neon-backed Replit database)
- **Authentication**: Replit Auth integration with OAuth2
- **File Uploads**: Pillow for image processing, uploads stored in `static/uploads/`

### Database Schema
- **users**: User profiles with admin/owner roles
- **projects**: Portfolio projects with status, categories, and stats
- **categories**: Project categorization system
- **tags**: Tag system for projects (many-to-many via project_tags)
- **comments**: User comments on projects
- **likes**: User likes for projects
- **notifications**: System notifications for users
- **about**: About page content management
- **flask_dance_oauth**: OAuth session management

### Frontend
- **Templates**: Jinja2 templates in `templates/` directory
- **Static Files**: CSS and JavaScript in `static/` directory
- **Features**: Responsive design, project galleries, admin dashboard

### Key Features
1. **Public Portfolio**: Browse published projects, categories, and tags
2. **User Authentication**: Secure login via Replit Auth
3. **Project Management**: CRUD operations for portfolio projects
4. **Admin Dashboard**: Administrative interface for content management
5. **Social Features**: Comments, likes, and notifications
6. **File Uploads**: Image upload system for project media
7. **Search & Filter**: Project search and category/tag filtering

### Configuration
- **Environment Variables**: 
  - `DATABASE_URL`: PostgreSQL connection string
  - `SESSION_SECRET`: Flask session security key
  - `REPL_ID`: Replit authentication configuration
- **File Storage**: Local uploads in `static/uploads/`
- **Debug Mode**: Enabled for development

### Deployment
- **Target**: Autoscale (stateless web application)
- **Command**: `python main.py`
- **Port**: 5000 (configured for 0.0.0.0 binding)

## User Preferences
- Project follows Flask best practices and conventions
- Uses PostgreSQL as the database backend
- Configured for Replit hosting environment
- Ready for production deployment with autoscale