"""Add the sample courses in seed_data/courses.json to the current database."""

import argparse
import json
import sys
from pathlib import Path

from sqlalchemy import select

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

from app import create_app
from app.auth.models import User
from app.courses import service
from app.courses.models import Course
from app.extensions import db


COURSES_FILE = BACKEND_DIR / "seed_data" / "courses.json"


def main():
    parser = argparse.ArgumentParser(description="Seed the LearnHub sample courses.")
    parser.add_argument("--admin-id", type=int, required=True)
    args = parser.parse_args()

    with COURSES_FILE.open(encoding="utf-8") as file:
        courses = json.load(file)

    app = create_app()
    with app.app_context():
        admin = db.session.get(User, args.admin_id)
        if admin is None or admin.role != "admin":
            raise SystemExit("The supplied user ID does not belong to an admin.")

        # Confirm all local image files exist before writing any course rows.
        uploads_folder = Path(app.instance_path) / "uploads" / "courses"
        missing = set()
        for course in courses:
            for image_url in (course.get("image"), course.get("instructorImage")):
                if image_url:
                    filename = image_url.rsplit("/", 1)[-1]
                    if not (uploads_folder / filename).is_file():
                        missing.add(filename)
        if missing:
            raise SystemExit("Missing image files: " + ", ".join(sorted(missing)))

        added = 0
        skipped = 0
        for course_data in courses:
            existing_id = db.session.scalar(
                select(Course.id).where(Course.title == course_data["title"])
            )
            if existing_id is not None:
                skipped += 1
                print("Skipped existing course:", course_data["title"])
                continue

            try:
                service.create_course(admin.id, course_data)
                added += 1
                print("Added:", course_data["title"])
            except Exception as error:
                db.session.rollback()
                raise SystemExit(
                    f"Stopped while adding {course_data['title']}: {error}"
                ) from error

        print(f"Finished. Added {added}; skipped {skipped} existing courses.")


if __name__ == "__main__":
    main()

