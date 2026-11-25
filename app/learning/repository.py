from sqlalchemy import delete, func, select
from sqlalchemy.orm import joinedload, selectinload

from app.courses.models import Course, CourseSection, Lesson
from app.extensions import db
from app.learning.models import Enrollment, Favorite, LessonProgress


def get_enrollment(user_id, course_id):
    statement = select(Enrollment).where(
        Enrollment.user_id == user_id,
        Enrollment.course_id == course_id,
    )
    return db.session.execute(statement).scalar_one_or_none()


def get_enrollments_for_user(user_id, page, page_size):
    total_items = db.session.scalar(
        select(func.count(Enrollment.id)).where(Enrollment.user_id == user_id)
    ) or 0
    statement = (
        select(Enrollment)
        .where(Enrollment.user_id == user_id)
        .options(
            joinedload(Enrollment.course)
            .joinedload(Course.sections)
            .joinedload(CourseSection.lessons)
        )
        .order_by(Enrollment.enrolled_at.desc(), Enrollment.id.desc())
        .limit(page_size)
        .offset((page - 1) * page_size)
    )
    items = db.session.execute(statement).unique().scalars().all()
    return items, total_items


def get_favorite_course_ids(user_id, course_ids):
    if not course_ids:
        return set()

    statement = select(Favorite.course_id).where(
        Favorite.user_id == user_id,
        Favorite.course_id.in_(course_ids),
    )
    return set(db.session.execute(statement).scalars().all())


def add_enrollment(enrollment):
    db.session.add(enrollment)
    db.session.flush()
    return enrollment


def get_favorite(user_id, course_id):
    statement = select(Favorite).where(
        Favorite.user_id == user_id,
        Favorite.course_id == course_id,
    )
    return db.session.execute(statement).scalar_one_or_none()


def get_favorites_for_user(user_id, page, page_size):
    total_items = db.session.scalar(
        select(func.count(Favorite.id)).where(Favorite.user_id == user_id)
    ) or 0
    statement = (
        select(Favorite)
        .where(Favorite.user_id == user_id)
        .options(
            selectinload(Favorite.course)
            .selectinload(Course.sections)
            .selectinload(CourseSection.lessons)
        )
        .order_by(Favorite.created_at.desc(), Favorite.id.desc())
        .limit(page_size)
        .offset((page - 1) * page_size)
    )
    items = db.session.execute(statement).scalars().all()
    return items, total_items


def add_favorite(favorite):
    db.session.add(favorite)
    db.session.flush()
    return favorite


def delete_favorite(favorite):
    db.session.delete(favorite)


def get_progress_for_course(user_id, course_id):
    statement = (
        select(LessonProgress)
        .join(Lesson, LessonProgress.lesson_id == Lesson.id)
        .join(CourseSection, Lesson.section_id == CourseSection.id)
        .where(
            LessonProgress.user_id == user_id,
            CourseSection.course_id == course_id,
        )
    )
    records = db.session.execute(statement).scalars().all()
    return {record.lesson_id: record.is_done for record in records}


def get_lesson_in_course(lesson_id, course_id):
    statement = (
        select(Lesson)
        .join(CourseSection, Lesson.section_id == CourseSection.id)
        .where(
            Lesson.id == lesson_id,
            CourseSection.course_id == course_id,
        )
    )
    return db.session.execute(statement).scalar_one_or_none()


def get_lesson_progress(user_id, lesson_id):
    statement = select(LessonProgress).where(
        LessonProgress.user_id == user_id,
        LessonProgress.lesson_id == lesson_id,
    )
    return db.session.execute(statement).scalar_one_or_none()


def delete_course_progress(user_id, course_id):
    lesson_ids = (
        select(Lesson.id)
        .join(CourseSection, Lesson.section_id == CourseSection.id)
        .where(CourseSection.course_id == course_id)
    )
    statement = delete(LessonProgress).where(
        LessonProgress.user_id == user_id,
        LessonProgress.lesson_id.in_(lesson_ids),
    )
    db.session.execute(statement.execution_options(synchronize_session=False))


def delete_enrollment(enrollment):
    db.session.delete(enrollment)


def save_changes():
    db.session.commit()


def rollback_changes():
    db.session.rollback()
