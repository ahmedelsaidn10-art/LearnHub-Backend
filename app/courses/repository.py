from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from app.courses.models import Course, CourseSection
from app.extensions import db


def get_published_courses(page, page_size):
    """Return one page of published courses in catalog order."""
    conditions = Course.is_published.is_(True)
    total_items = db.session.scalar(
        select(func.count(Course.id)).where(conditions)
    ) or 0
    statement = (
        select(Course)
        .where(conditions)
        .options(selectinload(Course.sections).selectinload(CourseSection.lessons))
        .order_by(Course.sort_order, Course.id)
        .limit(page_size)
        .offset((page - 1) * page_size)
    )
    items = db.session.execute(statement).scalars().all()
    return items, total_items


def get_course_by_id(course_id):
    return db.session.get(Course, course_id)


def add_course(course):
    db.session.add(course)
    db.session.flush()
    return course


def save_changes():
    db.session.commit()


def rollback_changes():
    db.session.rollback()
