from fastapi import APIRouter, status

from autosales.api.deps import SessionDep
from autosales.schemas import CarListItem
from autosales.services.catalog import CatalogService

router = APIRouter(prefix="/customers/{customer_id}/favorites", tags=["favorites"])


@router.get("", response_model=list[CarListItem])
async def list_favorites(customer_id: int, session: SessionDep):
    return await CatalogService(session).favorites(customer_id)


@router.put("/{car_id}", status_code=status.HTTP_204_NO_CONTENT)
async def add_favorite(customer_id: int, car_id: int, session: SessionDep) -> None:
    await CatalogService(session).add_favorite(customer_id, car_id)


@router.delete("/{car_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_favorite(customer_id: int, car_id: int, session: SessionDep) -> None:
    await CatalogService(session).remove_favorite(customer_id, car_id)
