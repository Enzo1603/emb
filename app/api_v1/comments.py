from flask import jsonify, request, g, url_for, current_app
from app import db
from app.models.comments_model import Comment
from app.models.roles_model import Permission
from app.models.posts_model import Post
from . import api_v1_bp
from .decorators import permission_required


@api_v1_bp.route('/comments/')
def get_comments():
    page = request.args.get('page', 1, type=int)
    pagination = Comment.query.order_by(Comment.timestamp.desc()).paginate(
        page,
        per_page=current_app.config['EMB_COMMENTS_PER_PAGE'],
        error_out=False,
    )
    comments = pagination.items
    prev = None
    if pagination.has_prev:
        prev = url_for('api_v1_bp.get_comments', page=page-1)

    next_page = None
    if pagination.has_next:
        next_page = url_for('api_v1_bp.get_comments', page=page+1)

    return jsonify({
        'comments': [comment.to_json() for comment in comments],
        'prev': prev,
        'next': next_page,
        'count': pagination.total,
    })


@api_v1_bp.route('/comments/<int:id>')
def get_comment(id):
    comment = Comment.query.get_or_404(id)
    return jsonify(comment.to_json())


@api_v1_bp.route('/posts/<int:id>/comments/')
def get_post_comments(id):
    post = Post.query.get_or_404(id)
    page = request.args.get('page', 1, type=int)
    pagination = post.comments.order_by(Comment.timestamp.asc()).paginate(
        page,
        per_page=current_app.config['EMB_COMMENTS_PER_PAGE'],
        error_out=False,
    )
    comments = pagination.items
    prev = None
    if pagination.has_prev:
        prev = url_for('api_v1_bp.get_post_comments', id=id, page=page-1)
    next_page = None
    if pagination.has_next:
        next_page = url_for('api_v1_bp.get_post_comments', id=id, page=page+1)
    return jsonify({
        'comments': [comment.to_json() for comment in comments],
        'prev': prev,
        'next': next_page,
        'count': pagination.total,
    })


@api_v1_bp.route('/posts/<int:id>/comments/', methods=['POST'])
@permission_required(Permission.COMMENT)
def new_post_comment(id):
    post = Post.query.get_or_404(id)
    comment = Comment.from_json(request.json)
    comment.author = g.current_user
    comment.post = post
    db.session.add(comment)
    db.session.commit()
    return jsonify(comment.to_json()), 201, \
        {'Location': url_for('api_v1_bp.get_comment', id=comment.id)}
