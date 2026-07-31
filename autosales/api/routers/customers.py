from fastapi import APIRouter
from sqlalchemy import select

from autosales.api.deps import SessionDep
from autosales.models import Customer, Location, utc_now
from autosales.schemas import CustomerCreate, CustomerRead, LocationRead

router = APIRouter(tags=["customers"])


@router.post("/customers", response_model=CustomerRead)
async def upsert_customer(data: CustomerCreate, session: SessionDep) -> Customer:
    customer = await session.scalar(
        select(Customer).where(Customer.telegram_id == data.telegram_id)
    )
    if customer is None:
        customer = Customer(**data.model_dump())
        session.add(customer)
    else:
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(customer, key, value)
        customer.last_activity_at = utc_now()
    await session.commit()
    await session.refresh(customer)
    return customer


@router.get("/locations", response_model=list[LocationRead])
async def list_locations(session: SessionDep) -> list[Location]:
    return list(
        (
            await session.scalars(
                select(Location).where(Location.is_active.is_(True)).order_by(Location.id)
            )
        ).all()
    )
