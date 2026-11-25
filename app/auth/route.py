from flask import Blueprint

from app.auth import controller


auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")

auth_bp.add_url_rule("/register", view_func=controller.register, methods=["POST"])
auth_bp.add_url_rule(
    "/verify-email", view_func=controller.verify_email, methods=["POST"]
)
auth_bp.add_url_rule(
    "/resend-verification",
    view_func=controller.resend_verification_code,
    methods=["POST"],
)
auth_bp.add_url_rule("/login", view_func=controller.login, methods=["POST"])
auth_bp.add_url_rule("/me", view_func=controller.current_user, methods=["GET"])
# Logout stays public so it can clear cookies even if the JWT is expired or missing.
auth_bp.add_url_rule("/logout", view_func=controller.logout, methods=["POST"])
