"""Replace placeholder locations with the two official sales sites.

Revision ID: 0002
Revises: 0001
"""

from sqlalchemy import text

from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    connection = op.get_bind()
    location_ids = list(
        connection.execute(text("SELECT id FROM locations ORDER BY id LIMIT 2")).scalars()
    )
    official_locations = (
        ("Kavto 1", "Полтава", "вул. Київське шосе, 41А"),
        ("Kavto 2", "Полтава", "вул. Механізаторів, 1А"),
    )
    for location_id, (name, city, address) in zip(location_ids, official_locations, strict=False):
        connection.execute(
            text(
                "UPDATE locations SET name = :name, city = :city, address = :address "
                "WHERE id = :location_id"
            ),
            {
                "location_id": location_id,
                "name": name,
                "city": city,
                "address": address,
            },
        )
    if len(location_ids) > 1:
        connection.execute(
            text(
                "UPDATE cars SET location_id = :second_location_id "
                "WHERE description ILIKE '%механізатор%' "
                "OR description ILIKE '%майданчик 2%' "
                "OR description ILIKE '%2 майданчик%' "
                "OR description ILIKE '%площадка 2%' "
                "OR description ILIKE '%2 площадка%'"
            ),
            {"second_location_id": location_ids[1]},
        )
    connection.execute(
        text(
            "UPDATE cars SET description = NULL "
            "WHERE description ILIKE '%Можливий продаж в кредит або лізинг%' "
            "OR btrim(description) IN ('-', '/start')"
        )
    )
    connection.execute(
        text("UPDATE knowledge_documents SET content = :content WHERE document_type = 'locations'"),
        {
            "content": (
                "Майданчик 1: вул. Київське шосе, 41А, Пн–Сб 09:00–19:00. "
                "Майданчик 2: вул. Механізаторів, 1А, Пн–Нд 09:00–19:00."
            )
        },
    )


def downgrade() -> None:
    # Official addresses are business data and must not be restored to placeholders.
    pass
