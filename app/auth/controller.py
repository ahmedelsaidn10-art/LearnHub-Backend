from flask import current_app, jsonify, request
from flask_jwt_extended import (
    get_jwt_identity,
    jwt_required,
    set_access_cookies,
    unset_jwt_cookies,
)

from app.auth import service
from app.auth.service import AuthError


def _request_data():
    """Read a JSON object from the request body."""
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise AuthError("Send the request data as a JSON object.")
    return data


def _success_response(result=None, status_code=200, message=None):
    """Return successful auth responses in one consistent format."""
    data = None

    if isinstance(result, dict):
        message = message or result.get("message")
        data = result.get("data")
        if data is None:
            data = {
                key: value
                for key, value in result.items()
                if key not in {"message", "access_token"}
            }
            if not data:
                data = None
    elif result is not None:
        data = result

    response_body = {
        "success": True,
        "message": message or "Request completed successfully.",
        "data": data,
    }
    return jsonify(response_body), status_code


def _error_response(error):
    """Turn service errors into safe, consistent JSON responses."""
    if isinstance(error, AuthError):
        return jsonify({
            "success": False,
            "message": error.message,
            "data": None,
        }), error.status_code

    current_app.logger.exception("Unexpected error in an auth controller.")
    return jsonify({
        "success": False,
        "message": "An unexpected server error occurred.",
        "data": None,
    }), 500


def register():
    try:
        data = _request_data()
        result = service.register_user(
            name=data.get("name"),
            email=data.get("email"),
            password=data.get("password"),
        )
        return _success_response(result, status_code=201)
    except Exception as error:
        return _error_response(error)


def resend_verification_code():
    try:
        data = _request_data()
        result = service.resend_verification_code(email=data.get("email"))
        return _success_response(result)
    except Exception as error:
        return _error_response(error)


def verify_email():
    try:
        data = _request_data()
        result = service.verify_email(
            email=data.get("email"),
            code=data.get("code"),
        )
        return _success_response(result)
    except Exception as error:
        return _error_response(error)


def login():
    try:
        data = _request_data()
        result = service.login_user(
            email=data.get("email"),
            password=data.get("password"),
        )

        # Keep the JWT in an HttpOnly cookie instead of returning it in JSON.
        response, status_code = _success_response(
            {"user": result["user"]},
            message="Login successful.",
        )
        set_access_cookies(response, result["access_token"])
        return response, status_code
    except Exception as error:
        return _error_response(error)


@jwt_required(optional=True)
def current_user():
    try:
        user_id = get_jwt_identity()
        if user_id is None:
            return _success_response(message="No user is currently logged in.")

        user = service.get_current_user(user_id)
        return _success_response({"user": user}, message="User details loaded.")
    except Exception as error:
        return _error_response(error)


def logout():
    """Clear the auth cookies, even if the JWT is missing or expired."""
    response, status_code = _success_response(message="You have been logged out.")
    unset_jwt_cookies(response)
    return response, status_code