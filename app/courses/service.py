from decimal import Decimal, InvalidOperation
import random

from app.auth import repository as auth_repository
from app.courses import repository
from app.courses.models import Course, CourseSection, Lesson
from app.courses.storage import save_course_image
from app.extensions import db
from app.pagination import PAGE_SIZE, page_data, parse_page


class CourseError(Exception):
    """An expected course error with an HTTP status for the controller."""

    def __init__(self, message, status_code=400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def _admin_user(user_id):
    try:
        user_id = int(user_id)
    except (TypeError, ValueError) as error:
        raise CourseError("A valid login is required.", 401) from error

    user = auth_repository.get_user_by_id(user_id)
    if user is None:
        raise CourseError("Your session is no longer valid. Please log in again.", 401)
    if user.role != "admin":
        raise CourseError("Only an admin can manage courses.", 403)
    return user


def _required_text(data, field, max_length=None):
    value = data.get(field)
    if not isinstance(value, str) or not value.strip():
        raise CourseError(f"{field} is required.")
    value = value.strip()
    if max_length is not None and len(value) > max_length:
        raise CourseError(f"{field} is too long.")
    return value


def _optional_text(data, field, max_length=None):
    value = data.get(field)
    if value is None or value == "":
        return None
    if not isinstance(value, str):
        raise CourseError(f"{field} must be text.")
    value = value.strip()
    if max_length is not None and len(value) > max_length:
        raise CourseError(f"{field} is too long.")
    return value or None


def _non_negative_integer(data, field, default=0):
    value = data.get(field, default)
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise CourseError(f"{field} must be a non-negative whole number.")
    return value


def _string_list(data, field):
    values = data.get(field, [])
    if not isinstance(values, list) or any(not isinstance(item, str) for item in values):
        raise CourseError(f"{field} must be a list of text values.")
    return [item.strip() for item in values if item.strip()]


def _course_details(data):
    details = data.get("details", {})
    if not isinstance(details, dict):
        raise CourseError("details must be a JSON object.")
    return details


def _make_course(data):
    details = _course_details(data)
    try:
        price = Decimal(str(data.get("price", 0)))
    except (InvalidOperation, ValueError) as error:
        raise CourseError("price must be a valid number.") from error
    if not price.is_finite() or price < 0:
        raise CourseError("price must be zero or greater.")

    sort_order = data.get("published", 0)
    if isinstance(sort_order, bool) or not isinstance(sort_order, int) or sort_order < 0:
        raise CourseError("published must be a non-negative sort order.")
    is_published = data.get("is_published", True)
    if not isinstance(is_published, bool):
        raise CourseError("is_published must be true or false.")

    curriculum = details.get("curriculum", [])
    if not isinstance(curriculum, list):
        raise CourseError("details.curriculum must be a list.")

    student_count = random.randint(100, 20000)
    review_count = random.randint(0, min(student_count, 2000))
    rating = Decimal(random.randint(35, 50)) / Decimal("10")

    course = Course(
        title=_required_text(data, "title", 180),
        category=_required_text(data, "category", 100),
        level=_required_text(data, "level", 40),
        price=price,
        description=_required_text(details, "description"),
        instructor_name=_required_text(data, "instructor", 120),
        instructor_title=_optional_text(details, "instructorTitle", 160),
        instructor_image_url=_optional_text(data, "instructorImage", 1000),
        image_url=_optional_text(data, "image", 1000),
        duration=_optional_text(data, "duration", 80) or "",
        label=_optional_text(data, "label", 80),
        sort_order=sort_order,
        is_published=is_published,
        rating=rating,
        review_count=review_count,
        display_student_count=student_count,
        display_favorite_count=random.randint(100, 5000),
        language=_optional_text(details, "language", 80) or "English",
        subtitles=_string_list(details, "subtitles"),
        repository_count=_non_negative_integer(details, "repositoryCount"),
        project_count=_non_negative_integer(details, "projectCount"),
        outcomes=_string_list(details, "outcomes"),
        requirements=_string_list(details, "requirements"),
    )

    for section_position, section_data in enumerate(curriculum, 1):
        if not isinstance(section_data, dict):
            raise CourseError("Each curriculum section must be a JSON object.")
        section_title = _required_text(section_data, "title", 180)
        lesson_titles = section_data.get("lessons", [])
        if not isinstance(lesson_titles, list):
            raise CourseError("Each section lessons value must be a list.")

        section = CourseSection(title=section_title, position=section_position)
        for lesson_position, lesson_data in enumerate(lesson_titles, 1):
            if isinstance(lesson_data, str):
                lesson_title = lesson_data.strip()
                lesson_description = ""
            elif isinstance(lesson_data, dict):
                lesson_title = _required_text(lesson_data, "title", 180)
                lesson_description = lesson_data.get("description", "")
                if not isinstance(lesson_description, str):
                    raise CourseError("Lesson description must be text.")
            else:
                raise CourseError("Each lesson must be a title or a JSON object.")

            if not lesson_title:
                raise CourseError("Lesson titles cannot be empty.")
            section.lessons.append(
                Lesson(
                    title=lesson_title,
                    description=lesson_description,
                    position=lesson_position,
                )
            )
        course.sections.append(section)

    return course


def course_data(course, user_id=None, include_lesson_ids=False):
    curriculum = []
    lesson_count = 0
    is_enrolled = False
    progress_by_lesson = {}

    if include_lesson_ids and user_id is not None:
        from app.learning import repository as learning_repository

        try:
            user_id = int(user_id)
        except (TypeError, ValueError):
            user_id = None
        is_enrolled = user_id is not None and learning_repository.get_enrollment(user_id, course.id) is not None
        if is_enrolled:
            progress_by_lesson = learning_repository.get_progress_for_course(user_id, course.id)

    for section in course.sections:
        lessons = []
        for lesson in section.lessons:
            lesson_count += 1
            if include_lesson_ids:
                lesson_data = {"id": lesson.id, "title": lesson.title}
                lesson_data["completed"] = (
                    bool(progress_by_lesson.get(lesson.id, False)) if is_enrolled else None
                )
                lessons.append(lesson_data)
            else:
                lessons.append(lesson.title)
        curriculum.append({"title": section.title, "lessons": lessons})

    updated_at = course.updated_at.strftime("%B %Y") if course.updated_at else ""
    data = {
        "id": course.id,
        "title": course.title,
        "category": course.category,
        "level": course.level,
        "price": float(course.price),
        "rating": float(course.rating),
        "reviewCount": course.review_count,
        "students": course.display_student_count,
        "favoriteCount": course.display_favorite_count,
        "duration": course.duration,
        "lessons": lesson_count,
        "instructor": course.instructor_name,
        "instructorImage": course.instructor_image_url,
        "image": course.image_url,
        "label": course.label or "",
        "published": course.sort_order,
        "is_published": course.is_published,
        "details": {
            "description": course.description,
            "instructorTitle": course.instructor_title or "",
            "updatedAt": updated_at,
            "language": course.language,
            "subtitles": course.subtitles or [],
            "repositoryCount": course.repository_count,
            "projectCount": course.project_count,
            "outcomes": course.outcomes or [],
            "requirements": course.requirements or [],
            "curriculum": curriculum,
        },
    }
    if include_lesson_ids:
        data["is_enrolled"] = is_enrolled
    return data

def list_courses(page_value=None):
    try:
        page = parse_page(page_value)
    except ValueError as error:
        raise CourseError(str(error)) from error

    courses, total_items = repository.get_published_courses(page, PAGE_SIZE)
    return {
        "items": [course_data(course) for course in courses],
        "pagination": page_data(page, total_items),
    }


def get_course(course_id, user_id=None):
    course = repository.get_course_by_id(course_id)
    if course is None or not course.is_published:
        raise CourseError("Course was not found.", 404)
    return course_data(course, user_id, include_lesson_ids=True)


def create_course(user_id, data):
    _admin_user(user_id)
    course = _make_course(data)
    try:
        repository.add_course(course)
        repository.save_changes()
    except Exception:
        repository.rollback_changes()
        raise
    return course_data(course)


def update_course(user_id, course_id, data):
    _admin_user(user_id)
    course = repository.get_course_by_id(course_id)
    if course is None:
        raise CourseError("Course was not found.", 404)
    if not isinstance(data, dict) or not data:
        raise CourseError("Send course fields to update.")

    details_patch = data.get("details", {})
    if not isinstance(details_patch, dict):
        raise CourseError("details must be a JSON object.")
    curriculum_changed = "curriculum" in details_patch
    has_progress = any(
        lesson.progress_records
        for section in course.sections
        for lesson in section.lessons
    )
    if curriculum_changed and (course.enrollments or has_progress):
        raise CourseError("The curriculum cannot be changed after students enroll or make progress.", 409)

    current_data = course_data(course)
    updated_data = {
        **current_data,
        **{key: value for key, value in data.items() if key != "details"},
        "details": {**current_data["details"], **details_patch},
    }
    updated_course = _make_course(updated_data)

    try:
        course.title = updated_course.title
        course.category = updated_course.category
        course.level = updated_course.level
        course.price = updated_course.price
        course.description = updated_course.description
        course.instructor_name = updated_course.instructor_name
        course.instructor_title = updated_course.instructor_title
        course.instructor_image_url = updated_course.instructor_image_url
        course.image_url = updated_course.image_url
        course.duration = updated_course.duration
        course.label = updated_course.label
        course.sort_order = updated_course.sort_order
        course.is_published = updated_course.is_published
        course.language = updated_course.language
        course.subtitles = updated_course.subtitles
        course.repository_count = updated_course.repository_count
        course.project_count = updated_course.project_count
        course.outcomes = updated_course.outcomes
        course.requirements = updated_course.requirements
        if curriculum_changed:
            course.sections.clear()
            course.sections.extend(updated_course.sections)
        repository.save_changes()
    except Exception:
        repository.rollback_changes()
        raise
    return course_data(course)
def delete_course(user_id, course_id):
    _admin_user(user_id)
    course = repository.get_course_by_id(course_id)
    if course is None:
        raise CourseError("Course was not found.", 404)
    try:
        db.session.delete(course)
        repository.save_changes()
    except Exception:
        repository.rollback_changes()
        raise


def upload_course_image(user_id, image_file):
    """Allow admins to upload an image for a course."""
    _admin_user(user_id)
    if image_file is None or not image_file.filename:
        raise CourseError("Choose an image file to upload.")
    try:
        return save_course_image(image_file)
    except OSError as error:
        raise CourseError("The image could not be saved on the server.", 500) from error




