from flask import Blueprint

from app.courses import controller


courses_bp = Blueprint("courses", __name__, url_prefix="/api/courses")
uploads_bp = Blueprint("course_uploads", __name__, url_prefix="/uploads/courses")

courses_bp.add_url_rule("", view_func=controller.list_courses, methods=["GET"])
courses_bp.add_url_rule("/<int:course_id>", view_func=controller.get_course, methods=["GET"])
courses_bp.add_url_rule("/image", view_func=controller.upload_course_image, methods=["POST"])
courses_bp.add_url_rule("", view_func=controller.create_course, methods=["POST"])
courses_bp.add_url_rule("/<int:course_id>", view_func=controller.update_course, methods=["PUT"])
courses_bp.add_url_rule("/<int:course_id>", view_func=controller.delete_course, methods=["DELETE"])

uploads_bp.add_url_rule("/<path:filename>", view_func=controller.serve_course_image, methods=["GET"])