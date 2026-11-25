from datetime import datetime, timezone
from sqlalchemy.exc import IntegrityError

from app.auth import repository as auth_repository
from app.courses import repository as course_repository
from app.courses import service as course_service
from app.extensions import db
from app.learning import repository
from app.learning.models import Enrollment, Favorite, LessonProgress
from app.pagination import PAGE_SIZE, page_data, parse_page


class LearningError(Exception):
    """An expected learning error with an HTTP status for the controller."""

    def __init__(self, message, status_code=400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def _current_student(user_id):
    try:
        user_id = int(user_id)
    except (TypeError, ValueError) as error:
        raise LearningError("A valid login is required.", 401) from error

    user = auth_repository.get_user_by_id(user_id)
    if user is None:
        raise LearningError("Your session is no longer valid. Please log in again.", 401)
    if not user.email_verified:
        raise LearningError("Verify your email before using your courses.", 403)
    return user_id


def _course_progress(course, user_id):
    lesson_count = sum(len(section.lessons) for section in course.sections)
    progress = repository.get_progress_for_course(user_id, course.id)
    completed_count = sum(progress.values())
    percentage = round(completed_count * 100 / lesson_count) if lesson_count else 0
    return {
        "completedLessons": completed_count,
        "totalLessons": lesson_count,
        "percentage": percentage,
    }


def add_course(user_id, data):
    user_id = _current_student(user_id)
    if not isinstance(data, dict):
        raise LearningError("Send the request data as a JSON object.")

    course_id = data.get("course_id")
    if isinstance(course_id, bool):
        raise LearningError("course_id must be a positive whole number.")
    try:
        course_id = int(course_id)
    except (TypeError, ValueError) as error:
        raise LearningError("course_id must be a positive whole number.") from error
    if course_id <= 0:
        raise LearningError("course_id must be a positive whole number.")

    course = course_repository.get_course_by_id(course_id)
    if course is None or not course.is_published:
        raise LearningError("Course was not found.", 404)
    if repository.get_enrollment(user_id, course_id):
        raise LearningError("This course is already in your courses.", 409)

    try:
        enrollment = Enrollment(user_id=user_id, course_id=course_id)
        repository.add_enrollment(enrollment)
        repository.save_changes()
    except IntegrityError as error:
        repository.rollback_changes()
        raise LearningError("This course is already in your courses.", 409) from error
    except Exception:
        repository.rollback_changes()
        raise

    total_lessons = sum(len(section.lessons) for section in course.sections)
    return {
        "course": course_service.course_data(course, user_id, include_lesson_ids=True),
        "enrolledAt": enrollment.enrolled_at.isoformat() if enrollment.enrolled_at else None,
        "progress": {
            "completedLessons": 0,
            "totalLessons": total_lessons,
            "percentage": 0,
        },
    }


def list_my_courses(user_id, page_value=None):
    user_id = _current_student(user_id)
    try:
        page = parse_page(page_value)
    except ValueError as error:
        raise LearningError(str(error)) from error

    enrollments, total_items = repository.get_enrollments_for_user(
        user_id,
        page,
        PAGE_SIZE,
    )
    favorite_course_ids = repository.get_favorite_course_ids(
        user_id,
        [enrollment.course_id for enrollment in enrollments],
    )

    result = []
    for enrollment in enrollments:
        course = enrollment.course
        course_data = course_service.course_data(course, user_id, include_lesson_ids=True)
        course_data["is_favorite"] = course.id in favorite_course_ids
        course_data["enrolledAt"] = (
            enrollment.enrolled_at.isoformat() if enrollment.enrolled_at else None
        )
        course_data["progress"] = _course_progress(course, user_id)
        result.append(course_data)

    return {
        "items": result,
        "pagination": page_data(page, total_items),
    }


def _favorite_course_id(value):
    if isinstance(value, bool):
        raise LearningError("course_id must be a positive whole number.")
    try:
        course_id = int(value)
    except (TypeError, ValueError) as error:
        raise LearningError("course_id must be a positive whole number.") from error
    if course_id <= 0:
        raise LearningError("course_id must be a positive whole number.")
    return course_id


def add_favorite(user_id, data):
    user_id = _current_student(user_id)
    if not isinstance(data, dict):
        raise LearningError("Send the request data as a JSON object.")

    course_id = _favorite_course_id(data.get("course_id"))
    course = course_repository.get_course_by_id(course_id)
    if course is None:
        raise LearningError("Course was not found.", 404)
    if repository.get_favorite(user_id, course_id):
        raise LearningError("This course is already in your favorites.", 409)

    try:
        favorite = Favorite(user_id=user_id, course_id=course_id)
        repository.add_favorite(favorite)
        repository.save_changes()
    except IntegrityError as error:
        repository.rollback_changes()
        raise LearningError("This course is already in your favorites.", 409) from error
    except Exception:
        repository.rollback_changes()
        raise

    return course_service.course_data(course)


def list_favorites(user_id, page_value=None):
    user_id = _current_student(user_id)
    try:
        page = parse_page(page_value)
    except ValueError as error:
        raise LearningError(str(error)) from error

    favorites, total_items = repository.get_favorites_for_user(
        user_id,
        page,
        PAGE_SIZE,
    )
    return {
        "items": [course_service.course_data(favorite.course) for favorite in favorites],
        "pagination": page_data(page, total_items),
    }


def remove_favorite(user_id, course_id):
    user_id = _current_student(user_id)
    course_id = _favorite_course_id(course_id)
    favorite = repository.get_favorite(user_id, course_id)
    if favorite is None:
        raise LearningError("This course is not in your favorites.", 404)

    try:
        repository.delete_favorite(favorite)
        repository.save_changes()
    except Exception:
        repository.rollback_changes()
        raise

def update_lesson_progress(user_id, course_id, lesson_id, data):
    user_id = _current_student(user_id)
    enrollment = repository.get_enrollment(user_id, course_id)
    if enrollment is None:
        raise LearningError(
            "Add this course to My Courses before updating lesson progress.",
            403,
        )

    lesson = repository.get_lesson_in_course(lesson_id, course_id)
    if lesson is None:
        raise LearningError("Lesson was not found in this course.", 404)

    if not isinstance(data, dict) or not isinstance(data.get("completed"), bool):
        raise LearningError("completed must be true or false.")

    progress = repository.get_lesson_progress(user_id, lesson_id)
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    try:
        if data["completed"]:
            if progress is None:
                progress = LessonProgress(
                    user_id=user_id,
                    lesson_id=lesson_id,
                    is_done=True,
                    completed_at=now,
                )
                db.session.add(progress)
            else:
                progress.is_done = True
                progress.completed_at = now
        elif progress is not None:
            db.session.delete(progress)

        repository.save_changes()
    except Exception:
        repository.rollback_changes()
        raise

    return {
        "courseId": course_id,
        "lessonId": lesson_id,
        "completed": data["completed"],
        "progress": _course_progress(enrollment.course, user_id),
    }


def remove_course(user_id, course_id):
    user_id = _current_student(user_id)
    enrollment = repository.get_enrollment(user_id, course_id)
    if enrollment is None:
        raise LearningError("This course is not in your courses.", 404)

    try:
        repository.delete_course_progress(user_id, course_id)
        repository.delete_enrollment(enrollment)
        repository.save_changes()
    except Exception:
        repository.rollback_changes()
        raise

