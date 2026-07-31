from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from autosales.models import AuditLog


async def record_audit(
    session: AsyncSession,
    *,
    user_id: str,
    action: str,
    entity_type: str,
    entity_id: str | int,
    old_value: dict[str, Any] | None = None,
    new_value: dict[str, Any] | None = None,
) -> AuditLog:
    entry = AuditLog(
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=str(entity_id),
        old_value=old_value,
        new_value=new_value,
    )
    session.add(entry)
    return entry
