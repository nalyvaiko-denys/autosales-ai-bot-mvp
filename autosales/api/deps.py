import secrets
from typing import Annotated

from fastapi import Depends, Header, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from autosales.ai.provider import LLMProvider
from autosales.config import Settings, get_settings
from autosales.db import get_session

SessionDep = Annotated[AsyncSession, Depends(get_session)]
SettingsDep = Annotated[Settings, Depends(get_settings)]


def get_ai_provider(request: Request) -> LLMProvider:
    return request.app.state.ai_provider


AIProviderDep = Annotated[LLMProvider, Depends(get_ai_provider)]


async def require_staff(
    settings: SettingsDep,
    authorization: Annotated[str | None, Header()] = None,
) -> str:
    expected = settings.staff_api_token.get_secret_value()
    supplied = authorization.removeprefix("Bearer ") if authorization else ""
    if not supplied or not secrets.compare_digest(supplied, expected):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid staff credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return "api:staff"


StaffDep = Annotated[str, Depends(require_staff)]
