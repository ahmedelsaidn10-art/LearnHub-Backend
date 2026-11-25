from email.message import EmailMessage
import smtplib
import ssl

from flask import current_app


class EmailSendError(Exception):
    """Raised when SMTP settings are missing or the email cannot be sent."""


def send_verification_code(email, code, expiry_minutes):
    """Send the OTP using the SMTP settings from the app configuration."""
    config = current_app.config
    host = config.get("SMTP_HOST")
    username = config.get("SMTP_USERNAME")
    password = config.get("SMTP_PASSWORD")
    sender = config.get("MAIL_FROM") or username
    port = config.get("SMTP_PORT", 587)

    if not host or not username or not password or not sender:
        raise EmailSendError("SMTP settings are missing.")

    message = EmailMessage()
    message["Subject"] = "Verify your LearnHub email"
    message["From"] = sender
    message["To"] = email
    message.set_content(
        f"Your LearnHub verification code is: {code}\n\n"
        f"This code expires in {expiry_minutes} minutes."
    )

    try:
        if config.get("SMTP_USE_SSL", False):
            with smtplib.SMTP_SSL(
                host, port, context=ssl.create_default_context(), timeout=20
            ) as server:
                server.login(username, password)
                server.send_message(message)
        else:
            with smtplib.SMTP(host, port, timeout=20) as server:
                server.starttls(context=ssl.create_default_context())
                server.login(username, password)
                server.send_message(message)
    except (OSError, smtplib.SMTPException) as error:
        raise EmailSendError("SMTP could not send the verification email.") from error
