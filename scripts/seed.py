import asyncio

from sqlalchemy import select

from autosales.db import SessionFactory
from autosales.enums import StaffRole
from autosales.models import KnowledgeDocument, Location, Manager


async def seed() -> None:
    async with SessionFactory() as session:
        if await session.scalar(select(Location.id).limit(1)):
            print("Seed skipped: data already exists")
            return
        podil = Location(
            name="Kavto 1",
            address="вул. Київське шосе, 41А",
            city="city",
            phone="+380440000001",
            working_hours="Пн–Сб 09:00–19:00",
        )
        left_bank = Location(
            name="Kavto 2",
            address="вул. Механізаторів, 1А",
            city="city",
            phone="+380440000002",
            working_hours="Пн–Нд 09:00–19:00",
        )
        session.add_all([podil, left_bank])
        await session.flush()
        session.add_all(
            [
                Manager(
                    name="B",
                    email="b@example.com",
                    location_id=podil.id,
                    role=StaffRole.MANAGER,
                ),
                Manager(
                    name="D",
                    email="d@example.com",
                    location_id=left_bank.id,
                    role=StaffRole.MANAGER,
                ),
            ]
        )
        session.add_all(
            [
                KnowledgeDocument(
                    title="Графік та адреси",
                    document_type="locations",
                    content=(
                        "Майданчик 1: вул. Київське шосе, 41А, Пн–Сб 09:00–19:00. "
                        "Майданчик 2: вул. Механізаторів, 1А, Пн–Нд 09:00–19:00."
                    ),
                ),
                KnowledgeDocument(
                    title="Правила тест-драйву",
                    document_type="test_drive",
                    content=(
                        "Тест-драйв доступний після підтвердження менеджером. Необхідні "
                        "посвідчення водія та документ, що посвідчує особу."
                    ),
                ),
                KnowledgeDocument(
                    title="Резервування",
                    document_type="reservation",
                    content=(
                        "Умови та строк резервування погоджуються з менеджером і фіксуються "
                        "після підтвердження клієнтом."
                    ),
                ),
            ]
        )
        await session.commit()
        print("Seed complete: 2 locations, 2 managers, 0 demo cars, 3 knowledge documents")


def main() -> None:
    asyncio.run(seed())


if __name__ == "__main__":
    main()
