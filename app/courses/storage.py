from pathlib import Path
from uuid import uuid4

from flask import current_app
from werkzeug.utils import secure_filename


def save_course_image(image_file):
    """Save an uploaded course image using a generated safe filename."""
    original_name = secure_filename(image_file.filename or "")
    extension = Path(original_name).suffix.lower()
    filename = f"{uuid4().hex}{extension}"

    upload_folder = Path(current_app.instance_path) / "uploads" / "courses"
    upload_folder.mkdir(parents=True, exist_ok=True)
    image_file.save(upload_folder / filename)

    return f"/uploads/courses/{filename}"