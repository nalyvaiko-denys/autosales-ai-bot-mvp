from typing import Annotated

from fastapi import APIRouter, Query, status

from autosales.api.deps import SessionDep, StaffDep
from autosales.models import Car
from autosales.schemas import (
    CarCreate,
    CarRead,
    CarSearchFilters,
    CarUpdate,
    PaginatedCars,
)
from autosales.services.catalog import CatalogService
from autosales.services.inventory import (
    archive_car as archive_inventory_car,
)
from autosales.services.inventory import (
    create_car as create_inventory_car,
)
from autosales.services.inventory import (
    update_car as update_inventory_car,
)

router = APIRouter(prefix="/cars", tags=["cars"])


@router.get("", response_model=PaginatedCars)
async def list_cars(
    session: SessionDep,
    filters: Annotated[CarSearchFilters, Query()],
) -> PaginatedCars:
    return await CatalogService(session).search(filters)


@router.get("/{car_id}", response_model=CarRead)
async def car_details(car_id: int, session: SessionDep) -> Car:
    return await CatalogService(session).get(car_id)


@router.post("", response_model=CarRead, status_code=status.HTTP_201_CREATED)
async def create_car(data: CarCreate, session: SessionDep, actor: StaffDep) -> Car:
    return await create_inventory_car(session, data, actor)


@router.patch("/{car_id}", response_model=CarRead)
async def update_car(car_id: int, data: CarUpdate, session: SessionDep, actor: StaffDep) -> Car:
    return await update_inventory_car(session, car_id, data, actor)


@router.delete("/{car_id}", status_code=status.HTTP_204_NO_CONTENT)
async def archive_car(car_id: int, session: SessionDep, actor: StaffDep) -> None:
    await archive_inventory_car(session, car_id, actor)
