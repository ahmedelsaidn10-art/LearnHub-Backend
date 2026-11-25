"""Add full course details and curriculum sections.

Revision ID: 286beed24739
Revises: 4a348775b834
"""
from alembic import op
import sqlalchemy as sa


revision = "286beed24739"
down_revision = "4a348775b834"
branch_labels = None
depends_on = None


def _inspector():
    return sa.inspect(op.get_bind())


def _has_column(table_name, column_name):
    return column_name in {column["name"] for column in _inspector().get_columns(table_name)}


def _has_index(table_name, index_name):
    return index_name in {index["name"] for index in _inspector().get_indexes(table_name)}


def _has_table(table_name):
    return table_name in _inspector().get_table_names()


def upgrade():
    # These checks also let the migration resume after MySQL's non-transactional DDL.
    if not _has_table("course_sections"):
        op.create_table(
            "course_sections",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("course_id", sa.Integer(), nullable=False),
            sa.Column("title", sa.String(length=180), nullable=False),
            sa.Column("position", sa.Integer(), nullable=False),
            sa.ForeignKeyConstraint(["course_id"], ["courses.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("course_id", "position", name="uq_sections_course_position"),
        )
    if not _has_index("course_sections", "ix_course_sections_course_id"):
        op.create_index("ix_course_sections_course_id", "course_sections", ["course_id"])

    course_columns = [
        ("instructor_title", sa.String(length=160), True, None),
        ("instructor_image_url", sa.String(length=1000), True, None),
        ("duration", sa.String(length=80), False, ""),
        ("label", sa.String(length=80), True, None),
        ("sort_order", sa.Integer(), False, "0"),
        ("rating", sa.Numeric(precision=2, scale=1), False, "4.5"),
        ("review_count", sa.Integer(), False, "0"),
        ("display_student_count", sa.Integer(), False, "0"),
        ("language", sa.String(length=80), False, "English"),
        ("subtitles", sa.JSON(), True, None),
        ("repository_count", sa.Integer(), False, "0"),
        ("project_count", sa.Integer(), False, "0"),
        ("outcomes", sa.JSON(), True, None),
        ("requirements", sa.JSON(), True, None),
        ("updated_at", sa.DateTime(), False, sa.text("CURRENT_TIMESTAMP")),
    ]
    for name, column_type, nullable, server_default in course_columns:
        if not _has_column("courses", name):
            op.add_column(
                "courses",
                sa.Column(name, column_type, nullable=nullable, server_default=server_default),
            )

    for name in ("subtitles", "outcomes", "requirements"):
        op.execute(f"UPDATE courses SET {name} = JSON_ARRAY() WHERE {name} IS NULL")
        if _inspector().get_columns("courses")[[c["name"] for c in _inspector().get_columns("courses")].index(name)]["nullable"]:
            op.alter_column("courses", name, existing_type=sa.JSON(), nullable=False)

    if not _has_column("lessons", "section_id"):
        op.add_column("lessons", sa.Column("section_id", sa.Integer(), nullable=True))

    # Existing lessons are placed in a default section without changing lesson IDs.
    op.execute(
        "INSERT INTO course_sections (course_id, title, position) "
        "SELECT DISTINCT lesson.course_id, 'Course content', 1 "
        "FROM lessons AS lesson "
        "WHERE NOT EXISTS (SELECT 1 FROM course_sections AS section "
        "WHERE section.course_id = lesson.course_id)"
    )
    op.execute(
        "UPDATE lessons AS lesson "
        "JOIN course_sections AS section ON section.course_id = lesson.course_id "
        "SET lesson.section_id = section.id WHERE lesson.section_id IS NULL"
    )
    lesson_columns = _inspector().get_columns("lessons")
    section_column = next(column for column in lesson_columns if column["name"] == "section_id")
    if section_column["nullable"]:
        op.alter_column("lessons", "section_id", existing_type=sa.Integer(), nullable=False)

    # MySQL requires dropping the foreign key before its supporting unique index.
    for foreign_key in _inspector().get_foreign_keys("lessons"):
        if foreign_key["constrained_columns"] == ["course_id"] and foreign_key["name"]:
            op.drop_constraint(foreign_key["name"], "lessons", type_="foreignkey")

    for index in _inspector().get_indexes("lessons"):
        if index["column_names"] == ["course_id", "position"] and index["unique"]:
            op.drop_index(index["name"], table_name="lessons")
        elif index["name"] == "ix_lessons_course_id":
            op.drop_index(index["name"], table_name="lessons")

    if not _has_index("lessons", "ix_lessons_section_id"):
        op.create_index("ix_lessons_section_id", "lessons", ["section_id"])
    if not _has_index("lessons", "uq_lessons_section_position"):
        op.create_unique_constraint(
            "uq_lessons_section_position", "lessons", ["section_id", "position"]
        )
    if not any(
        foreign_key["constrained_columns"] == ["section_id"]
        for foreign_key in _inspector().get_foreign_keys("lessons")
    ):
        op.create_foreign_key(
            "fk_lessons_section_id_course_sections",
            "lessons",
            "course_sections",
            ["section_id"],
            ["id"],
            ondelete="CASCADE",
        )
    if _has_column("lessons", "course_id"):
        op.drop_column("lessons", "course_id")


def downgrade():
    op.add_column("lessons", sa.Column("course_id", sa.Integer(), nullable=True))
    op.execute(
        "UPDATE lessons AS lesson "
        "JOIN course_sections AS section ON section.id = lesson.section_id "
        "SET lesson.course_id = section.course_id"
    )
    op.alter_column("lessons", "course_id", existing_type=sa.Integer(), nullable=False)
    op.drop_constraint("fk_lessons_section_id_course_sections", "lessons", type_="foreignkey")
    op.drop_constraint("uq_lessons_section_position", "lessons", type_="unique")
    op.drop_index("ix_lessons_section_id", table_name="lessons")
    op.create_foreign_key(
        "lessons_ibfk_1",
        "lessons",
        "courses",
        ["course_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_index("uq_lessons_course_position", "lessons", ["course_id", "position"], unique=True)
    op.drop_column("lessons", "section_id")

    op.drop_index("ix_course_sections_course_id", table_name="course_sections")
    op.drop_table("course_sections")
    for column in (
        "updated_at", "requirements", "outcomes", "project_count", "repository_count",
        "subtitles", "language", "display_student_count", "review_count", "rating",
        "sort_order", "label", "duration", "instructor_image_url", "instructor_title",
    ):
        op.drop_column("courses", column)