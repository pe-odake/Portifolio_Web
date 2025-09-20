# routes.py - Main application routes
import os
import uuid
from datetime import datetime
from urllib.parse import urlparse
from werkzeug.utils import secure_filename

from flask import (
    render_template, request, redirect, url_for, flash, 
    jsonify, session, abort, current_app
)
from flask_login import current_user
from sqlalchemy import desc, func

from app import app, db
from models import (
    Project, Category, Tag, ProjectTag, Comment, 
    Like, About, Notification, User, ProjectStatus
)
from replit_auth import require_login, make_replit_blueprint, admin_required, owner_required

# Register the Replit Auth blueprint
app.register_blueprint(make_replit_blueprint(), url_prefix="/auth")

# Make session permanent
@app.before_request
def make_session_permanent():
    session.permanent = True

# Helper functions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in current_app.config.get('ALLOWED_EXTENSIONS', set())

def get_upload_filename(filename):
    """Generate a unique filename for uploads"""
    ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
    unique_filename = f"{uuid.uuid4().hex}.{ext}"
    return unique_filename

# PUBLIC ROUTES

@app.route('/')
def index():
    """Homepage - shows featured projects and latest projects"""
    if not current_user.is_authenticated:
        # Landing page for non-authenticated users
        return render_template('landing.html')
    
    # Featured projects
    featured_projects = Project.query.filter_by(
        status=ProjectStatus.PUBLISHED, 
        is_featured=True
    ).limit(3).all()
    
    # Latest projects
    latest_projects = Project.query.filter_by(
        status=ProjectStatus.PUBLISHED
    ).order_by(desc(Project.created_at)).limit(6).all()
    
    # Popular projects (most liked)
    popular_projects = Project.query.filter_by(
        status=ProjectStatus.PUBLISHED
    ).order_by(desc(Project.likes_count)).limit(3).all()
    
    # Categories
    categories = Category.query.all()
    
    return render_template('index.html', 
                         featured_projects=featured_projects,
                         latest_projects=latest_projects,
                         popular_projects=popular_projects,
                         categories=categories)

@app.route('/projects')
def projects():
    """List all published projects with filters"""
    page = request.args.get('page', 1, type=int)
    category_id = request.args.get('category', type=int)
    tag_name = request.args.get('tag')
    search_query = request.args.get('q', '')
    
    # Base query
    query = Project.query.filter_by(status=ProjectStatus.PUBLISHED)
    
    # Apply filters
    if category_id:
        query = query.filter_by(category_id=category_id)
    
    if tag_name:
        tag = Tag.query.filter_by(name=tag_name).first()
        if tag:
            query = query.join(ProjectTag).filter(ProjectTag.tag_id == tag.id)
    
    if search_query:
        query = query.filter(
            db.or_(
                Project.title.contains(search_query),
                Project.description.contains(search_query)
            )
        )
    
    # Pagination
    projects_pagination = query.order_by(desc(Project.created_at)).paginate(
        page=page, per_page=9, error_out=False
    )
    
    categories = Category.query.all()
    tags = Tag.query.all()
    
    return render_template('projects.html',
                         projects=projects_pagination.items,
                         pagination=projects_pagination,
                         categories=categories,
                         tags=tags,
                         current_category=category_id,
                         current_tag=tag_name,
                         search_query=search_query)

@app.route('/project/<int:project_id>')
def project_detail(project_id):
    """Show project details"""
    project = Project.query.filter_by(
        id=project_id, 
        status=ProjectStatus.PUBLISHED
    ).first_or_404()
    
    # Increment view count
    project.views += 1
    db.session.commit()
    
    # Get comments
    comments = Comment.query.filter_by(project_id=project_id).order_by(desc(Comment.created_at)).all()
    
    # Check if current user liked this project
    user_liked = False
    if current_user.is_authenticated:
        user_liked = Like.query.filter_by(
            user_id=current_user.id, 
            project_id=project_id
        ).first() is not None
    
    # Get project tags
    project_tags = db.session.query(Tag).join(ProjectTag).filter(
        ProjectTag.project_id == project_id
    ).all()
    
    # Similar projects (same category, excluding current)
    similar_projects = Project.query.filter(
        Project.category_id == project.category_id,
        Project.id != project_id,
        Project.status == ProjectStatus.PUBLISHED
    ).limit(3).all()
    
    return render_template('project_detail.html',
                         project=project,
                         comments=comments,
                         user_liked=user_liked,
                         project_tags=project_tags,
                         similar_projects=similar_projects)

@app.route('/about')
def about():
    """About page"""
    about_info = About.query.first()
    return render_template('about.html', about=about_info)

# AUTHENTICATED USER ROUTES

@app.route('/like/<int:project_id>', methods=['POST'])
@require_login
def toggle_like(project_id):
    """Toggle like for a project"""
    project = Project.query.get_or_404(project_id)
    
    existing_like = Like.query.filter_by(
        user_id=current_user.id,
        project_id=project_id
    ).first()
    
    if existing_like:
        # Unlike
        db.session.delete(existing_like)
        project.likes_count = max(0, project.likes_count - 1)
        liked = False
    else:
        # Like
        like = Like(user_id=current_user.id, project_id=project_id)
        db.session.add(like)
        project.likes_count += 1
        liked = True
        
        # Create notification for project owner
        if project.author_id != current_user.id:
            notification = Notification(
                title="New Like",
                message=f"{current_user.first_name or 'Someone'} liked your project '{project.title}'",
                type="success",
                user_id=project.author_id
            )
            db.session.add(notification)
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'liked': liked,
        'likes_count': project.likes_count
    })

@app.route('/comment/<int:project_id>', methods=['POST'])
@require_login
def add_comment(project_id):
    """Add a comment to a project"""
    project = Project.query.get_or_404(project_id)
    content = request.form.get('content', '').strip()
    
    if not content:
        flash('Comment cannot be empty', 'error')
        return redirect(url_for('project_detail', project_id=project_id))
    
    comment = Comment(
        content=content,
        user_id=current_user.id,
        project_id=project_id
    )
    
    db.session.add(comment)
    project.comments_count += 1
    
    # Create notification for project owner
    if project.author_id != current_user.id:
        notification = Notification(
            title="New Comment",
            message=f"{current_user.first_name or 'Someone'} commented on your project '{project.title}'",
            type="info",
            user_id=project.author_id
        )
        db.session.add(notification)
    
    db.session.commit()
    flash('Comment added successfully', 'success')
    
    return redirect(url_for('project_detail', project_id=project_id))

@app.route('/profile')
@require_login
def profile():
    """User profile page"""
    user_projects = Project.query.filter_by(author_id=current_user.id).all()
    user_comments = Comment.query.filter_by(user_id=current_user.id).count()
    user_likes = Like.query.filter_by(user_id=current_user.id).count()
    
    return render_template('profile.html',
                         user_projects=user_projects,
                         user_comments=user_comments,
                         user_likes=user_likes)

# ADMIN ROUTES

@app.route('/admin')
@admin_required
def admin_dashboard():
    """Admin dashboard"""
    total_projects = Project.query.count()
    published_projects = Project.query.filter_by(status=ProjectStatus.PUBLISHED).count()
    draft_projects = Project.query.filter_by(status=ProjectStatus.DRAFT).count()
    total_users = User.query.count()
    total_comments = Comment.query.count()
    total_likes = Like.query.count()
    
    # Recent activity
    recent_projects = Project.query.order_by(desc(Project.created_at)).limit(5).all()
    recent_comments = Comment.query.order_by(desc(Comment.created_at)).limit(5).all()
    
    return render_template('admin/dashboard.html',
                         total_projects=total_projects,
                         published_projects=published_projects,
                         draft_projects=draft_projects,
                         total_users=total_users,
                         total_comments=total_comments,
                         total_likes=total_likes,
                         recent_projects=recent_projects,
                         recent_comments=recent_comments)

@app.route('/admin/projects')
@admin_required
def admin_projects():
    """Manage projects"""
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status')
    
    query = Project.query
    if status:
        if status == 'published':
            query = query.filter_by(status=ProjectStatus.PUBLISHED)
        elif status == 'draft':
            query = query.filter_by(status=ProjectStatus.DRAFT)
    
    projects = query.order_by(desc(Project.created_at)).paginate(
        page=page, per_page=10, error_out=False
    )
    
    return render_template('admin/projects.html', projects=projects)

@app.route('/admin/project/new')
@admin_required 
def admin_new_project():
    """Create new project form"""
    categories = Category.query.all()
    tags = Tag.query.all()
    return render_template('admin/project_form.html', 
                         project=None, 
                         categories=categories, 
                         tags=tags)

@app.route('/admin/project/edit/<int:project_id>')
@admin_required
def admin_edit_project(project_id):
    """Edit project form"""
    project = Project.query.get_or_404(project_id)
    categories = Category.query.all()
    tags = Tag.query.all()
    
    # Get current project tags
    project_tag_ids = [pt.tag_id for pt in project.project_tags]
    
    return render_template('admin/project_form.html', 
                         project=project, 
                         categories=categories, 
                         tags=tags,
                         project_tag_ids=project_tag_ids)

@app.route('/admin/project/save', methods=['POST'])
@admin_required
def admin_save_project():
    """Save project (create or update)"""
    project_id = request.form.get('project_id', type=int)
    
    if project_id:
        project = Project.query.get_or_404(project_id)
    else:
        project = Project(author_id=current_user.id)
    
    # Update project fields
    project.title = request.form.get('title', '').strip()
    project.description = request.form.get('description', '').strip()
    project.content = request.form.get('content', '').strip()
    project.github_url = request.form.get('github_url', '').strip()
    project.demo_url = request.form.get('demo_url', '').strip()
    project.category_id = request.form.get('category_id', type=int)
    project.is_featured = bool(request.form.get('is_featured'))
    
    # Handle status
    status = request.form.get('status')
    if status == 'published':
        project.status = ProjectStatus.PUBLISHED
    else:
        project.status = ProjectStatus.DRAFT
    
    # Handle file upload
    if 'image' in request.files:
        file = request.files['image']
        if file and file.filename and allowed_file(file.filename):
            filename = get_upload_filename(file.filename)
            filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            
            # Ensure upload directory exists
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            file.save(filepath)
            project.image_url = f'/static/uploads/{filename}'
    
    if not project_id:
        db.session.add(project)
    
    db.session.flush()  # Get project ID for new projects
    
    # Handle tags
    tag_ids = request.form.getlist('tags')
    if tag_ids:
        # Remove existing tags
        ProjectTag.query.filter_by(project_id=project.id).delete()
        
        # Add new tags
        for tag_id in tag_ids:
            project_tag = ProjectTag(project_id=project.id, tag_id=int(tag_id))
            db.session.add(project_tag)
    
    db.session.commit()
    flash('Project saved successfully', 'success')
    
    return redirect(url_for('admin_projects'))

@app.route('/admin/project/delete/<int:project_id>', methods=['POST'])
@admin_required
def admin_delete_project(project_id):
    """Delete project"""
    project = Project.query.get_or_404(project_id)
    db.session.delete(project)
    db.session.commit()
    flash('Project deleted successfully', 'success')
    
    return redirect(url_for('admin_projects'))

# ERROR HANDLERS

@app.errorhandler(403)
def forbidden(error):
    return render_template('403.html'), 403

@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500

# Context processors
@app.context_processor
def inject_globals():
    """Inject global template variables"""
    return {
        'current_year': datetime.now().year,
        'categories': Category.query.all(),
        'recent_projects': Project.query.filter_by(status=ProjectStatus.PUBLISHED).order_by(desc(Project.created_at)).limit(3).all()
    }