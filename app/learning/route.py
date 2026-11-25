from flask import Blueprint

from app.learning import controller


learning_bp = Blueprint("learning", __name__, url_prefix="/api/my-courses")

learning_bp.add_url_rule("", view_func=controller.list_my_courses, methods=["GET"])
learning_bp.add_url_rule("", view_func=controller.add_course, methods=["POST"])
learning_bp.add_url_rule(
    "/<int:course_id>/lessons/<int:lesson_id>",
    view_func=controller.update_lesson_progress,
    methods=["PATCH"],
)
learning_bp.add_url_rule(
    "/<int:course_id>",
    view_func=controller.remove_course,
    methods=["DELETE"],
)
