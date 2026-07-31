from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from autosales.models import Lead, Manager


async def manager_for_location(session: AsyncSession, location_id: int | None) -> Manager | None:
    """Pick the least-loaded active manager at a location for deterministic MVP assignment."""
    active_lead_count = func.count(Lead.id).label("active_leads")
    statement = (
        select(Manager)
        .outerjoin(Lead, Lead.manager_id == Manager.id)
        .where(Manager.is_active.is_(True), Manager.location_id == location_id)
        .group_by(Manager.id)
        .order_by(active_lead_count.asc(), Manager.id.asc())
        .limit(1)
    )
    return await session.scalar(statement)
