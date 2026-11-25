from pathlib import Path

from flask import current_app, jsonify, request, send_from_directory
from flask_jwt_extended import get_jwt_identity, jwt_required

from app.courses import service
from app.courses.service import CourseError


def _success_response(data=None, message="Request completed successfully.", status_code=200):
    return jsonify({"success": True, "message": message, "data": data}), status_code


def _error_response(error):
    if isinstance(error, CourseError):
        return jsonify({"success": False, "message": error.message, "data": None}), error.status_code
    current_app.logger.exception("Unexpected error in a courses controller.")
    return jsonify({
        "success": False,
        "message": "An unexpected server error occurred.",
        "data": None,
    }), 500


def _request_data():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise CourseError("Send the request data as a JSON object.")
    return data


def list_courses():
    try:
        return _success_response(service.list_courses(request.args.get("page")), "Courses loaded.")
    except Exception as error:
        return _error_response(error)


@jwt_required(optional=True)
def get_course(course_id):
    try:
        return _success_response(
            service.get_course(course_id, get_jwt_identity()),
            "Course loaded.",
        )
    except Exception as error:
        return _error_response(error)


@jwt_required()
def upload_course_image():
    try:
        image_url = service.upload_course_image(
            get_jwt_identity(),
            request.files.get("image"),
        )
        return _success_response(
            {"image_url": image_url},
            "Course image uploaded.",
            201,
        )
    except Exception as error:
        return _error_response(error)


def serve_course_image(filename):
    """Serve a previously uploaded course image from the instance folder."""
    upload_folder = Path(current_app.instance_path) / "uploads" / "courses"
    return send_from_directory(upload_folder, filename)


@jwt_required()
def create_course():
    try:
        course = service.create_course(get_jwt_identity(), _request_data())
        return _success_response(course, "Course created.", 201)
    except Exception as error:
        return _error_response(error)


@jwt_required()
def update_course(course_id):
    try:
        course = service.update_course(get_jwt_identity(), course_id, _request_data())
        return _success_response(course, "Course updated.")
    except Exception as error:
        return _error_response(error)


@jwt_required()
def delete_course(course_id):
    try:
        service.delete_course(get_jwt_identity(), course_id)
        return _success_response(message="Course deleted.")
    except Exception as error:
        return _error_response(error)

