from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from autosales.enums import AppointmentStatus, CarStatus, LeadStatus
from autosales.errors import NotFoundError, UnavailableCarError
from autosales.models import Appointment, Car, Customer, Lead
from autosales.schemas import AppointmentCreate, AppointmentUpdate
from autosales.services.assignment import manager_for_location
from autosales.services.audit import record_audit


class AppointmentService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, data: AppointmentCreate) -> Appointment:
        car = await self.session.get(Car, data.car_id, with_for_update=True)
        if car is None:
            raise NotFoundError("Автомобіль не знайдено")
        if car.status != CarStatus.AVAILABLE:
            raise UnavailableCarError("Автомобіль зараз недоступний для запису")
        customer = await self.session.get(Customer, data.customer_id)
        if customer is None:
            raise NotFoundError("Клієнта не знайдено")
        if data.appointment_at <= datetime.now().astimezone():
            raise UnavailableCarError("Дата зустрічі має бути в майбутньому")

        location_id = data.location_id or car.location_id
        if location_id != car.location_id:
            raise UnavailableCarError("Автомобіль перебуває на іншому майданчику")
        manager = await manager_for_location(self.session, location_id)
        appointment = Appointment(
            **data.model_dump(exclude={"location_id"}),
            location_id=location_id,
            manager_id=manager.id if manager else None,
        )
        self.session.add(appointment)
        await self.session.flush()
        await record_audit(
            self.session,
            user_id=f"customer:{data.customer_id}",
            action="appointment.create",
            entity_type="appointment",
            entity_id=appointment.id,
            new_value={"status": appointment.status.value, "car_id": data.car_id},
        )
        await self.session.commit()
        await self.session.refresh(appointment)
        return appointment

    async def update(self, appointment_id: int, data: AppointmentUpdate, actor: str) -> Appointment:
        appointment = await self.session.get(Appointment, appointment_id)
        if appointment is None:
            raise NotFoundError("Запис не знайдено")
        changes = data.model_dump(exclude_unset=True)
        old = {key: getattr(appointment, key) for key in changes}
        for key, value in changes.items():
            setattr(appointment, key, value)
        if data.status == AppointmentStatus.CONFIRMED:
            lead = await self.session.scalar(
                select(Lead)
                .where(
                    Lead.customer_id == appointment.customer_id,
                    Lead.car_id == appointment.car_id,
                )
                .order_by(Lead.created_at.desc())
                .limit(1)
            )
            if lead:
                lead.status = LeadStatus.APPOINTMENT_SCHEDULED
        await record_audit(
            self.session,
            user_id=actor,
            action="appointment.update",
            entity_type="appointment",
            entity_id=appointment.id,
            old_value={
                key: str(value) if value is not None else None for key, value in old.items()
            },
            new_value={
                key: str(value) if value is not None else None for key, value in changes.items()
            },
        )
        await self.session.commit()
        await self.session.refresh(appointment)
        return appointment

    async def claim_contact(
        self, appointment_id: int, *, actor: str, manager_id: int | None = None
    ) -> tuple[Appointment, bool]:
        appointment = await self.session.scalar(
            select(Appointment).where(Appointment.id == appointment_id).with_for_update()
        )
        if appointment is None:
            raise NotFoundError("Запис не знайдено")
        if appointment.status != AppointmentStatus.PENDING:
            return appointment, False
        appointment.status = AppointmentStatus.CONFIRMED
        if manager_id is not None:
            appointment.manager_id = manager_id
        await record_audit(
            self.session,
            user_id=actor,
            action="appointment.claim_contact",
            entity_type="appointment",
            entity_id=appointment.id,
            old_value={"status": AppointmentStatus.PENDING.value},
            new_value={
                "status": appointment.status.value,
                "manager_id": appointment.manager_id,
            },
        )
        await self.session.commit()
        await self.session.refresh(appointment)
        return appointment, True

    async def delete(self, appointment_id: int, *, actor: str) -> None:
        appointment = await self.session.scalar(
            select(Appointment).where(Appointment.id == appointment_id).with_for_update()
        )
        if appointment is None:
            raise NotFoundError("Запис не знайдено")
        await record_audit(
            self.session,
            user_id=actor,
            action="appointment.delete",
            entity_type="appointment",
            entity_id=appointment.id,
            old_value={
                "customer_id": appointment.customer_id,
                "car_id": appointment.car_id,
                "status": appointment.status.value,
                "appointment_at": appointment.appointment_at.isoformat(),
            },
        )
        await self.session.delete(appointment)
        await self.session.commit()
