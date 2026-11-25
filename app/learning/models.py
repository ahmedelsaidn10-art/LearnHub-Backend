from sqlalchemy import UniqueConstraint

from app.extensions import db


class Favorite(db.Model):
    """A course saved by a user."""

    __tablename__ = "favorites"
    __table_args__ = (
        UniqueConstraint("user_id", "course_id", name="uq_favorites_user_course"),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    course_id = db.Column(
        db.Integer,
        db.ForeignKey("courses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    created_at = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)

    user = db.relationship("User", back_populates="favorites")
    course = db.relationship("Course", back_populates="favorites")


class Enrollment(db.Model):
    """A course added to one user's My Courses list."""

    __tablename__ = "enrollments"
    __table_args__ = (
        UniqueConstraint("user_id", "course_id", name="uq_enrollments_user_course"),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    course_id = db.Column(
        db.Integer,
        db.ForeignKey("courses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    enrolled_at = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)

    user = db.relationship("User", back_populates="enrollments")
    course = db.relationship("Course", back_populates="enrollments")


class LessonProgress(db.Model):
    """Whether one user has completed one lesson."""

    __tablename__ = "lesson_progress"
    __table_args__ = (
        UniqueConstraint("user_id", "lesson_id", name="uq_progress_user_lesson"),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    lesson_id = db.Column(
        db.Integer,
        db.ForeignKey("lessons.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    is_done = db.Column(db.Boolean, default=False, nullable=False)
    completed_at = db.Column(db.DateTime)

    user = db.relationship("User", back_populates="lesson_progress")
    lesson = db.relationship("Lesson", back_populates="progress_records")
