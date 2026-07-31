from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from autosales.enums import LeadStatus
from autosales.errors import NotFoundError
from autosales.models import Car, Lead
from autosales.schemas import LeadCreate, LeadUpdate
from autosales.services.assignment import manager_for_location
from autosales.services.audit import record_audit


class LeadService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, data: LeadCreate) -> tuple[Lead, bool]:
        existing = await self.session.scalar(
            select(Lead).where(Lead.idempotency_key == data.idempotency_key)
        )
        if existing:
            return existing, False

        location_id = None
        if data.car_id is not None:
            car = await self.session.get(Car, data.car_id)
            if car is None:
                raise NotFoundError("Автомобіль не знайдено")
            location_id = car.location_id
        manager = await manager_for_location(self.session, location_id)
        lead = Lead(**data.model_dump(), manager_id=manager.id if manager else None)
        self.session.add(lead)
        try:
            await self.session.flush()
        except IntegrityError:
            await self.session.rollback()
            concurrent = await self.session.scalar(
                select(Lead).where(Lead.idempotency_key == data.idempotency_key)
            )
            if concurrent:
                return concurrent, False
            raise
        await record_audit(
            self.session,
            user_id=f"customer:{data.customer_id}",
            action="lead.create",
            entity_type="lead",
            entity_id=lead.id,
            new_value={"status": lead.status.value, "manager_id": lead.manager_id},
        )
        await self.session.commit()
        await self.session.refresh(lead)
        return lead, True

    async def update(self, lead_id: int, data: LeadUpdate, actor: str) -> Lead:
        lead = await self.session.get(Lead, lead_id)
        if lead is None:
            raise NotFoundError("Заявку не знайдено")
        changes = data.model_dump(exclude_unset=True)
        old = {key: getattr(lead, key) for key in changes}
        for key, value in changes.items():
            setattr(lead, key, value)
        await record_audit(
            self.session,
            user_id=actor,
            action="lead.update",
            entity_type="lead",
            entity_id=lead.id,
            old_value={
                key: str(value) if value is not None else None for key, value in old.items()
            },
            new_value={
                key: str(value) if value is not None else None for key, value in changes.items()
            },
        )
        await self.session.commit()
        await self.session.refresh(lead)
        return lead

    async def claim_contact(
        self, lead_id: int, *, actor: str, manager_id: int | None = None
    ) -> tuple[Lead, bool]:
        lead = await self.session.scalar(select(Lead).where(Lead.id == lead_id).with_for_update())
        if lead is None:
            raise NotFoundError("Звернення не знайдено")
        if lead.status not in {LeadStatus.NEW, LeadStatus.IN_PROGRESS}:
            return lead, False
        old_status = lead.status
        lead.status = LeadStatus.CONTACTED
        if manager_id is not None:
            lead.manager_id = manager_id
        lead.result = f"Менеджер почав зв’язок ({actor})"
        await record_audit(
            self.session,
            user_id=actor,
            action="lead.claim_contact",
            entity_type="lead",
            entity_id=lead.id,
            old_value={"status": old_status.value},
            new_value={"status": lead.status.value, "manager_id": lead.manager_id},
        )
        await self.session.commit()
        await self.session.refresh(lead)
        return lead, True

    async def delete(self, lead_id: int, *, actor: str) -> None:
        lead = await self.session.scalar(select(Lead).where(Lead.id == lead_id).with_for_update())
        if lead is None:
            raise NotFoundError("Звернення не знайдено")
        await record_audit(
            self.session,
            user_id=actor,
            action="lead.delete",
            entity_type="lead",
            entity_id=lead.id,
            old_value={
                "customer_id": lead.customer_id,
                "car_id": lead.car_id,
                "status": lead.status.value,
                "message": lead.message,
            },
        )
        await self.session.delete(lead)
        await self.session.commit()
