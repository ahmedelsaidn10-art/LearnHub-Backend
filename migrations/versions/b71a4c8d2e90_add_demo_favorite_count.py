"""Add a saved demo favorite count to courses.

Revision ID: b71a4c8d2e90
Revises: 286beed24739
"""
import random

from alembic import op
import sqlalchemy as sa


revision = "b71a4c8d2e90"
down_revision = "286beed24739"
branch_labels = None
depends_on = None


def _has_column(table_name, column_name):
    inspector = sa.inspect(op.get_bind())
    return column_name in {column["name"] for column in inspector.get_columns(table_name)}


def upgrade():
    if not _has_column("courses", "display_favorite_count"):
        op.add_column(
            "courses",
            sa.Column(
                "display_favorite_count",
                sa.Integer(),
                nullable=False,
                server_default=sa.text("0"),
            ),
        )

    # Give existing courses a stable demo number. The seeded generator keeps
    # retries safe if MySQL stops midway through its non-transactional DDL.
    connection = op.get_bind()
    course_ids = connection.execute(
        sa.text("SELECT id FROM courses WHERE display_favorite_count = 0")
    ).scalars()
    for course_id in course_ids:
        demo_count = random.Random(course_id).randint(100, 5000)
        connection.execute(
            sa.text(
                "UPDATE courses SET display_favorite_count = :count "
                "WHERE id = :course_id AND display_favorite_count = 0"
            ),
            {"count": demo_count, "course_id": course_id},
        )


def downgrade():
    if _has_column("courses", "display_favorite_count"):
        op.drop_column("courses", "display_favorite_count")

