"""Normalize Ukrainian vehicle values to stable internal codes.

Revision ID: 0003
Revises: 0002
"""

from sqlalchemy import text

from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    connection = op.get_bind()
    updates = {
        "fuel_type": {
            "бензин": "petrol",
            "дизель": "diesel",
            "газ": "gas",
            "lpg": "gas",
            "гібрид": "hybrid",
            "електро": "electric",
            "електрика": "electric",
        },
        "transmission": {
            "автомат": "automatic",
            "автоматична": "automatic",
            "акпп": "automatic",
            "механіка": "manual",
            "механічна": "manual",
            "мкпп": "manual",
        },
        "drive_type": {
            "повний": "awd",
            "повний привід": "awd",
            "передній": "fwd",
            "передній привід": "fwd",
            "задній": "rwd",
            "задній привід": "rwd",
            "не вказано": "not_specified",
        },
        "body_type": {
            "кросовер": "crossover",
            "позашляховик": "suv",
            "седан": "sedan",
            "хетчбек": "hatchback",
            "універсал": "wagon",
            "мінівен": "minivan",
            "купе": "coupe",
            "ліфтбек": "liftback",
            "не вказано": "not_specified",
        },
    }
    for column, replacements in updates.items():
        for source, target in replacements.items():
            connection.execute(
                text(f"UPDATE cars SET {column} = :target WHERE lower(btrim({column})) = :source"),
                {"source": source, "target": target},
            )


def downgrade() -> None:
    # Canonical codes are intentionally retained.
    pass
