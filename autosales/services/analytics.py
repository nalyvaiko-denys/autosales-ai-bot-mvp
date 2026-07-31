from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from autosales.enums import AppointmentStatus, CarStatus
from autosales.models import Appointment, Car, Customer, Lead
from autosales.schemas import AnalyticsSummary


async def analytics_summary(session: AsyncSession) -> AnalyticsSummary:
    customers = int((await session.scalar(select(func.count(Customer.id)))) or 0)
    leads = int((await session.scalar(select(func.count(Lead.id)))) or 0)
    appointments = int((await session.scalar(select(func.count(Appointment.id)))) or 0)
    completed_appointments = int(
        (
            await session.scalar(
                select(func.count(Appointment.id)).where(
                    Appointment.status == AppointmentStatus.COMPLETED
                )
            )
        )
        or 0
    )
    sold = int(
        (await session.scalar(select(func.count(Car.id)).where(Car.status == CarStatus.SOLD))) or 0
    )
    available = int(
        (await session.scalar(select(func.count(Car.id)).where(Car.status == CarStatus.AVAILABLE)))
        or 0
    )
    popular_rows = (
        await session.execute(
            select(Car.id, Car.brand, Car.model, Car.popularity)
            .order_by(Car.popularity.desc())
            .limit(5)
        )
    ).all()
    popular = [
        {"id": row.id, "name": f"{row.brand} {row.model}", "views": row.popularity}
        for row in popular_rows
    ]
    return AnalyticsSummary(
        customers=customers,
        leads=leads,
        appointments=appointments,
        sold_cars=sold,
        available_cars=available,
        lead_to_appointment_conversion=round(appointments / leads, 4) if leads else 0,
        appointment_to_sale_conversion=(
            round(sold / completed_appointments, 4) if completed_appointments else 0
        ),
        popular_cars=popular,
    )
