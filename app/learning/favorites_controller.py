from flask import current_app, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from app.learning import service
from app.learning.service import LearningError


def _success_response(data=None, message="Request completed successfully.", status_code=200):
    return jsonify({"success": True, "message": message, "data": data}), status_code


def _error_response(error):
    if isinstance(error, LearningError):
        return jsonify({"success": False, "message": error.message, "data": None}), error.status_code
    current_app.logger.exception("Unexpected error in a favorites controller.")
    return jsonify({
        "success": False,
        "message": "An unexpected server error occurred.",
        "data": None,
    }), 500


def _request_data():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise LearningError("Send the request data as a JSON object.")
    return data


@jwt_required()
def list_favorites():
    try:
        result = service.list_favorites(
            get_jwt_identity(),
            request.args.get("page"),
        )
        return _success_response(result, "Favorites loaded.")
    except Exception as error:
        return _error_response(error)


@jwt_required()
def add_favorite():
    try:
        result = service.add_favorite(get_jwt_identity(), _request_data())
        return _success_response(result, "Course added to favorites.", 201)
    except Exception as error:
        return _error_response(error)


@jwt_required()
def remove_favorite(course_id):
    try:
        service.remove_favorite(get_jwt_identity(), course_id)
        return _success_response(message="Course removed from favorites.")
    except Exception as error:
        return _error_response(error)
