"""Simplify inventory statuses and remove subjective search metadata.

Revision ID: 0004
Revises: 0003
"""

import sqlalchemy as sa

from alembic import op

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def _car_columns() -> set[str]:
    return {column["name"] for column in sa.inspect(op.get_bind()).get_columns("cars")}


def upgrade() -> None:
    # SQLAlchemy stores Enum member names in this schema. Lowercase values are
    # included for compatibility with any early/manual database installations.
    op.execute(
        """
        UPDATE cars
        SET status = CASE
            WHEN status IN ('DRAFT', 'draft') THEN 'ARCHIVED'
            WHEN status IN ('TEST_DRIVE', 'test_drive', 'SERVICE', 'service') THEN 'RESERVED'
            ELSE status
        END
        WHERE status IN ('DRAFT', 'draft', 'TEST_DRIVE', 'test_drive', 'SERVICE', 'service')
        """
    )

    # Remove only the four unmistakable demo listings from the former seed file.
    demo_vins = "'JTMBRREV0LD123456', 'JM3KFBDM1K0123456', 'TMBJG7NX1MY123456', 'KM8K22AA0LU123456'"
    op.execute(
        f"UPDATE leads SET car_id = NULL WHERE car_id IN (SELECT id FROM cars WHERE vin IN ({demo_vins}))"
    )
    for table in ("appointments", "generated_content", "favorites", "car_media"):
        op.execute(
            f"DELETE FROM {table} WHERE car_id IN (SELECT id FROM cars WHERE vin IN ({demo_vins}))"
        )
    op.execute(f"DELETE FROM cars WHERE vin IN ({demo_vins})")

    if "use_cases" in _car_columns():
        op.drop_column("cars", "use_cases")


def downgrade() -> None:
    if "use_cases" not in _car_columns():
        op.add_column("cars", sa.Column("use_cases", sa.Text(), nullable=True))
