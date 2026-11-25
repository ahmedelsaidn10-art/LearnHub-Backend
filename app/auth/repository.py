from app.auth.models import EmailOTP, User
from app.extensions import db


def get_user_by_email(email):
    """Find an account by its normalized email address."""
    return db.session.execute(
        db.select(User).where(User.email == email)
    ).scalar_one_or_none()


def get_user_by_id(user_id):
    """Find an account by its ID."""
    return db.session.get(User, user_id)


def add_user(user):
    """Add a new user to the current database transaction."""
    db.session.add(user)
    db.session.flush()
    return user


def get_otp_for_user(user_id):
    """Return the one current OTP row for a user, if it exists."""
    return db.session.get(EmailOTP, user_id)


def save_otp(user_id, code_hash, expires_at):
    """Create an OTP row or replace the user's old code and expiry."""
    otp = get_otp_for_user(user_id)

    if otp is None:
        otp = EmailOTP(user_id=user_id, code_hash=code_hash, expires_at=expires_at)
        db.session.add(otp)
    else:
        otp.code_hash = code_hash
        otp.expires_at = expires_at

    return otp


def delete_otp_for_user(user_id):
    """Delete the current OTP after successful verification or expiry."""
    otp = get_otp_for_user(user_id)

    if otp is not None:
        db.session.delete(otp)


def set_email_verified(user, is_verified=True):
    """Update the user's email verification status."""
    user.email_verified = is_verified
    return user


def commit_changes():
    """Save all changes staged by the service in one transaction."""
    db.session.commit()


def rollback_changes():
    """Undo staged changes if the service encounters an error."""
    db.session.rollback()


