from datetime import datetime, timedelta, timezone
import secrets

from email_validator import EmailNotValidError, validate_email
from flask import current_app
from flask_jwt_extended import create_access_token
from sqlalchemy.exc import IntegrityError
from werkzeug.security import check_password_hash, generate_password_hash

from app.auth import repository
from app.auth.email_service import EmailSendError, send_verification_code
from app.auth.models import User


class AuthError(Exception):
    """An expected authentication error that the controller can turn into JSON."""

    def __init__(self, message, status_code=400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def _normalize_email(email):
    if not isinstance(email, str) or not email.strip():
        raise AuthError("A valid email address is required.")

    try:
        return validate_email(email.strip(), check_deliverability=False).normalized.lower()
    except EmailNotValidError as error:
        raise AuthError("Enter a valid email address.") from error


def _make_otp():
    return f"{secrets.randbelow(1_000_000):06d}"


def _send_new_otp(user):
    """Store a fresh code, replacing any old code, then email it."""
    code = _make_otp()
    expiry_minutes = current_app.config["OTP_EXPIRY_MINUTES"]
    expires_at = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(
        minutes=expiry_minutes
    )
    code_hash = generate_password_hash(code)

    repository.save_otp(user.id, code_hash, expires_at)
    repository.commit_changes()

    try:
        send_verification_code(user.email, code, expiry_minutes)
    except EmailSendError as error:
        # The account and OTP remain saved so the user can request another code.
        raise AuthError(
            "We could not send the verification email. Please try again later.",
            503,
        ) from error


def register_user(name, email, password):
    """Create an unverified student account and send its first OTP."""
    if not isinstance(name, str) or not name.strip():
        raise AuthError("Name is required.")
    name = name.strip()
    if len(name) > 120:
        raise AuthError("Name must be 120 characters or fewer.")

    email = _normalize_email(email)
    if not isinstance(password, str) or len(password) < 8:
        raise AuthError("Password must be at least 8 characters long.")
    if len(password) > 128:
        raise AuthError("Password must be 128 characters or fewer.")

    if repository.get_user_by_email(email) is not None:
        raise AuthError("An account with this email already exists.", 409)

    user = User(name=name, email=email, role="student", email_verified=False)
    user.set_password(password)

    try:
        repository.add_user(user)
        _send_new_otp(user)
    except IntegrityError as error:
        repository.rollback_changes()
        raise AuthError("An account with this email already exists.", 409) from error
    except Exception:
        repository.rollback_changes()
        raise

    return {"message": "Your account was created. Check your email for the verification code."}


def resend_verification_code(email):
    """Replace the old OTP and send a new one for an unverified account."""
    email = _normalize_email(email)
    user = repository.get_user_by_email(email)

    if user is None:
        return {"message": "If the account can receive a code, a new code has been sent."}
    if user.email_verified:
        return {"message": "This account is already verified."}

    try:
        _send_new_otp(user)
    except Exception:
        repository.rollback_changes()
        raise

    return {"message": "A new verification code has been sent to your email."}


def verify_email(email, code):
    """Check the current OTP, verify the account, and remove the used code."""
    email = _normalize_email(email)
    user = repository.get_user_by_email(email)
    if user is None or user.email_verified:
        raise AuthError("The verification code is invalid or expired.")

    otp = repository.get_otp_for_user(user.id)
    if otp is None:
        raise AuthError("The verification code is invalid or expired.")

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    if otp.expires_at <= now:
        repository.delete_otp_for_user(user.id)
        repository.commit_changes()
        raise AuthError("The verification code is invalid or expired.")

    if not isinstance(code, str) or not check_password_hash(otp.code_hash, code):
        raise AuthError("The verification code is invalid or expired.")

    repository.set_email_verified(user)
    repository.delete_otp_for_user(user.id)
    repository.commit_changes()

    return {"message": "Your email has been verified. You can now log in."}


def login_user(email, password):
    """Check credentials and return a JWT for the controller to set as a cookie."""
    email = _normalize_email(email)
    user = repository.get_user_by_email(email)

    if user is None or not isinstance(password, str) or not user.check_password(password):
        raise AuthError("Invalid email or password.", 401)
    if not user.email_verified:
        raise AuthError("Verify your email before logging in.", 403)

    token = create_access_token(identity=str(user.id))
    return {
        "access_token": token,
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role,
        },
    }


def get_current_user(user_id):
    """Return safe account details for the user identified by a valid JWT."""
    try:
        user_id = int(user_id)
    except (TypeError, ValueError) as error:
        raise AuthError("Your session is invalid. Please log in again.", 401) from error

    user = repository.get_user_by_id(user_id)
    if user is None:
        raise AuthError("Your session is no longer valid. Please log in again.", 401)

    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "role": user.role,
    }