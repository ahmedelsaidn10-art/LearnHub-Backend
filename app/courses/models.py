from decimal import Decimal

from sqlalchemy import UniqueConstraint

from app.extensions import db


class Course(db.Model):
    """A course shown in the catalog and details page."""

    __tablename__ = "courses"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(180), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(100), nullable=False, index=True)
    level = db.Column(db.String(40), nullable=False)
    image_url = db.Column(db.String(1000))
    instructor_name = db.Column(db.String(120), nullable=False)
    instructor_title = db.Column(db.String(160))
    instructor_image_url = db.Column(db.String(1000))
    price = db.Column(db.Numeric(10, 2), default=Decimal("0.00"), nullable=False)
    duration = db.Column(db.String(80), nullable=False, default="")
    label = db.Column(db.String(80))
    sort_order = db.Column(db.Integer, default=0, nullable=False)
    is_published = db.Column(db.Boolean, default=True, nullable=False)
    rating = db.Column(db.Numeric(2, 1), default=Decimal("4.5"), nullable=False)
    review_count = db.Column(db.Integer, default=0, nullable=False)
    display_student_count = db.Column(db.Integer, default=0, nullable=False)
    display_favorite_count = db.Column(db.Integer, default=0, server_default="0", nullable=False)
    language = db.Column(db.String(80), nullable=False, default="English")
    subtitles = db.Column(db.JSON, nullable=False, default=list)
    repository_count = db.Column(db.Integer, default=0, nullable=False)
    project_count = db.Column(db.Integer, default=0, nullable=False)
    outcomes = db.Column(db.JSON, nullable=False, default=list)
    requirements = db.Column(db.JSON, nullable=False, default=list)
    created_at = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)
    updated_at = db.Column(
        db.DateTime,
        server_default=db.func.now(),
        onupdate=db.func.now(),
        nullable=False,
    )

    sections = db.relationship(
        "CourseSection",
        back_populates="course",
        cascade="all, delete-orphan",
        order_by="CourseSection.position",
    )
    favorites = db.relationship("Favorite", back_populates="course", cascade="all, delete-orphan")
    enrollments = db.relationship(
        "Enrollment", back_populates="course", cascade="all, delete-orphan"
    )


class CourseSection(db.Model):
    """A named group of lessons inside a course."""

    __tablename__ = "course_sections"
    __table_args__ = (
        UniqueConstraint("course_id", "position", name="uq_sections_course_position"),
    )

    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(
        db.Integer,
        db.ForeignKey("courses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title = db.Column(db.String(180), nullable=False)
    position = db.Column(db.Integer, nullable=False)

    course = db.relationship("Course", back_populates="sections")
    lessons = db.relationship(
        "Lesson",
        back_populates="section",
        cascade="all, delete-orphan",
        order_by="Lesson.position",
    )


class Lesson(db.Model):
    """A text and image lesson inside one course section."""

    __tablename__ = "lessons"
    __table_args__ = (
        UniqueConstraint("section_id", "position", name="uq_lessons_section_position"),
    )

    id = db.Column(db.Integer, primary_key=True)
    section_id = db.Column(
        db.Integer,
        db.ForeignKey("course_sections.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title = db.Column(db.String(180), nullable=False)
    description = db.Column(db.Text, nullable=False, default="")
    image_url = db.Column(db.String(1000))
    position = db.Column(db.Integer, nullable=False)

    section = db.relationship("CourseSection", back_populates="lessons")
    progress_records = db.relationship(
        "LessonProgress", back_populates="lesson", cascade="all, delete-orphan"
    )
