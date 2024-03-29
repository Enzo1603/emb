from flask import render_template, request, jsonify
from . import main_bp


@main_bp.app_errorhandler(403)
def forbidden(e):
    if request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html:
        response = jsonify({"error": "forbidden"})
        response.status_code = 403
        return response
    return render_template('main/errors.html', error_message=e), 403


@main_bp.app_errorhandler(404)
def page_not_found(e):
    if request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html:
        response = jsonify({"error": "not found"})
        response.status_code = 404
        return response
    return render_template('main/errors.html', error_message=e), 404


@main_bp.app_errorhandler(500)
def internal_server_error(e):
    if request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html:
        response = jsonify({"error": "internal server error"})
        response.status_code = 500
        return response
    return render_template('main/errors.html', error_message=e), 500
