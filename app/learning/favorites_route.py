from flask import Blueprint

from app.learning import favorites_controller


favorites_bp = Blueprint("favorites", __name__, url_prefix="/api/favorites")

favorites_bp.add_url_rule("", view_func=favorites_controller.list_favorites, methods=["GET"])
favorites_bp.add_url_rule("", view_func=favorites_controller.add_favorite, methods=["POST"])
favorites_bp.add_url_rule(
    "/<int:course_id>",
    view_func=favorites_controller.remove_favorite,
    methods=["DELETE"],
)
