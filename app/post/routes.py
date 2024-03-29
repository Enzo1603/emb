from flask import current_app, flash, make_response, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.models.users_model import User

from app.post.image_handler import upload_post_image

from app.post import post_bp
from app import db
from app.models.comments_model import Comment
from app.models.posts_model import Post
from app.models.roles_model import Permission
from app.post.forms import CommentForm, PostForm


@post_bp.route("/create-post/", methods=["GET", "POST"])
@login_required
def create_post():
    if not current_user.can(Permission.WRITE):
        flash("You do not have the permission to write posts.", "warning")
        return redirect(url_for("user_bp.profile", username=current_user.username))

    form = PostForm()
    if form.validate_on_submit():
        post = Post(
            title=form.title.data,
            raw_body=form.raw_body.data,
            author_id=current_user.id,
        )
        db.session.add(post)
        db.session.commit()

        if form.image.data:
            image_filename = upload_post_image(form.image.data, post.id)
            post.image = image_filename
            db.session.commit()

        return redirect(url_for("user_bp.profile", username=current_user.username))

    return render_template("post/create_post.html", form=form)


@post_bp.route("/posts/")
def posts():
    page = request.args.get("page", 1, type=int)
    show_followed = False
    if current_user.is_authenticated:
        show_followed = bool(request.cookies.get("show_followed", ""))
    if show_followed:
        query = current_user.followed_posts
    else:
        query = Post.query
    pagination = query.order_by(Post.timestamp.desc()).paginate(
        page,
        per_page=current_app.config["EMB_POSTS_PER_PAGE"],
        error_out=False,
    )
    posts = pagination.items
    return render_template("post/posts.html", posts=posts, pagination=pagination)


@post_bp.route("/all/")
@login_required
def show_all():
    resp = make_response(redirect(url_for("post_bp.posts")))
    resp.set_cookie("show_followed", "", max_age=30*24*60*60)  # 30 days
    return resp


@post_bp.route("/followed/")
@login_required
def show_followed():
    resp = make_response(redirect(url_for("post_bp.posts")))
    resp.set_cookie("show_followed", "1", max_age=30*24*60*60)  # 30 days
    return resp


@post_bp.route("/<string:username>/<int:post_id>/", methods=["GET", "POST"])
@login_required
def view_post(username, post_id):
    user = User.query.filter_by(username=username).first_or_404()
    post = Post.query.filter_by(id=post_id, author=user).first_or_404()

    form = CommentForm()
    if form.validate_on_submit():
        comment = Comment(
            raw_body=form.raw_body.data,
            author_id=current_user.id,
            post=post,
        )
        db.session.add(comment)
        db.session.commit()
        flash("Your comment has been published.", "success")
        return redirect(url_for("post_bp.view_post", username=user.username, post_id=post.id))
    page = request.args.get("page", 1, type=int)
    if page == -1:
        page = (post.comments.count() - 1) // current_app.config["EMB_COMMENTS_PER_PAGE"] + 1
    pagination = post.comments.order_by(Comment.timestamp.desc()).paginate(
        page,
        per_page=current_app.config["EMB_COMMENTS_PER_PAGE"],
        error_out=False
    )
    comments = pagination.items

    return render_template("post/view_post.html", post=post, user=user, form=form, comments=comments, pagination=pagination)


@post_bp.route("/<int:post_id>/edit/", methods=["GET", "POST"])
@login_required
def edit_post(post_id):
    post = Post.query.filter_by(id=post_id, author_id=current_user.id).first_or_404()

    form = PostForm()

    if form.validate_on_submit():
        post.title = form.title.data
        post.raw_body = form.raw_body.data
        if form.image.data:
            post.image = upload_post_image(form.image.data, post.id)

        db.session.commit()

    form.title.data = post.title
    form.raw_body.data = post.raw_body

    return render_template("post/edit_post.html", form=form)


@post_bp.route("/<int:post_id>/delete/")
@login_required
def delete_post(post_id):
    post_to_delete = Post.query.filter_by(id=post_id, author_id=current_user.id).first_or_404()
    comments_to_delete = Comment.query.filter_by(post_id=post_id).all()
    try:
        for comment_to_delete in comments_to_delete:
            db.session.delete(comment_to_delete)
        db.session.delete(post_to_delete)
        db.session.commit()
        flash("Post has been deleted successfully.", "success")
        return redirect(url_for("user_bp.profile", username=current_user.username))
    except:
        flash("Whoops! There was an error deleting the post...", "warning")
        return redirect(url_for("post_bp.view_post", username=current_user.username, post_id=post_id))
