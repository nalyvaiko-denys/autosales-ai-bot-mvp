import asyncio
from decimal import Decimal

from sqlalchemy import select

from autosales.db import SessionFactory
from autosales.enums import CarStatus, StaffRole
from autosales.models import Car, KnowledgeDocument, Location, Manager


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
        cars = [
            Car(
                brand="Toyota",
                model="RAV4",
                generation="XA50",
                year=2020,
                price=Decimal("19800"),
                mileage=72000,
                body_type="crossover",
                fuel_type="hybrid",
                transmission="automatic",
                drive_type="awd",
                engine_volume=Decimal("2.5"),
                color="white",
                vin="JTMBRREV0LD123456",
                description="Практичний кросовер із просторим салоном.",
                equipment="Клімат-контроль, камера заднього огляду, адаптивний круїз-контроль.",
                condition="Перевірений технічний стан.",
                use_cases="family city travel reliability economy",
                status=CarStatus.AVAILABLE,
                location_id=podil.id,
            ),
            Car(
                brand="Mazda",
                model="CX-5",
                generation="KF",
                year=2019,
                price=Decimal("18500"),
                mileage=86000,
                body_type="crossover",
                fuel_type="petrol",
                transmission="automatic",
                drive_type="awd",
                engine_volume=Decimal("2.5"),
                color="red",
                vin="JM3KFBDM1K0123456",
                description="Сімейний кросовер із якісним салоном.",
                equipment="Підігрів сидінь, LED-фари, контроль сліпих зон.",
                condition="Без зауважень за результатами діагностики.",
                use_cases="family city comfort safety",
                status=CarStatus.AVAILABLE,
                location_id=left_bank.id,
            ),
            Car(
                brand="Skoda",
                model="Octavia",
                generation="A8",
                year=2021,
                price=Decimal("14900"),
                mileage=64000,
                body_type="liftback",
                fuel_type="diesel",
                transmission="automatic",
                drive_type="fwd",
                engine_volume=Decimal("2.0"),
                color="gray",
                vin="TMBJG7NX1MY123456",
                description="Економний автомобіль для міста і поїздок трасою.",
                equipment="Двозонний клімат-контроль, CarPlay, парктроніки.",
                condition="Регламентне обслуговування виконано.",
                use_cases="city travel economy first_car",
                status=CarStatus.AVAILABLE,
                location_id=podil.id,
            ),
            Car(
                brand="Hyundai",
                model="Kona",
                generation="OS",
                year=2020,
                price=Decimal("15200"),
                mileage=51000,
                body_type="crossover",
                fuel_type="petrol",
                transmission="automatic",
                drive_type="fwd",
                engine_volume=Decimal("1.6"),
                color="blue",
                vin="KM8K22AA0LU123456",
                description="Компактний міський кросовер.",
                equipment="Камера, CarPlay, підігрів керма.",
                condition="Перевірений технічний стан.",
                use_cases="city first_car economy",
                status=CarStatus.AVAILABLE,
                location_id=left_bank.id,
            ),
        ]
        session.add_all(cars)
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
        print("Seed complete: 2 locations, 2 managers, 4 cars, 3 knowledge documents")


def main() -> None:
    asyncio.run(seed())


if __name__ == "__main__":
    main()
