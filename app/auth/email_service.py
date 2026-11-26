from email.message import EmailMessage
import json
import smtplib
import ssl
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from flask import current_app


class EmailSendError(Exception):
    """Raised when email settings are missing or a message cannot be sent."""


def _send_with_brevo(email, code, expiry_minutes, config):
    api_key = config.get("BREVO_API_KEY")
    sender = config.get("MAIL_FROM")
    if not api_key or not sender:
        raise EmailSendError("Brevo email settings are missing.")

    payload = {
        "sender": {
            "name": config.get("MAIL_FROM_NAME", "LearnHub"),
            "email": sender,
        },
        "to": [{"email": email}],
        "subject": "Verify your LearnHub email",
        "textContent": (
            f"Your LearnHub verification code is: {code}\n\n"
            f"This code expires in {expiry_minutes} minutes."
        ),
    }
    request = Request(
        "https://api.brevo.com/v3/smtp/email",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "accept": "application/json",
            "api-key": api_key,
            "content-type": "application/json",
        },
        method="POST",
    )

    try:
        with urlopen(request, timeout=20):
            pass
    except (HTTPError, URLError, OSError) as error:
        raise EmailSendError("Brevo could not send the verification email.") from error


def _send_with_smtp(email, code, expiry_minutes, config):
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


def send_verification_code(email, code, expiry_minutes):
    """Send an OTP using the configured provider."""
    config = current_app.config
    if config.get("EMAIL_PROVIDER", "smtp") == "brevo":
        _send_with_brevo(email, code, expiry_minutes, config)
        return
    _send_with_smtp(email, code, expiry_minutes, config)
