from fastapi import APIRouter, BackgroundTasks, status
from sqlalchemy import select

from autosales.api.deps import SessionDep, SettingsDep, StaffDep
from autosales.i18n import normalize_language, text
from autosales.localization import appointment_status_label
from autosales.models import Appointment, Customer
from autosales.schemas import AppointmentCreate, AppointmentRead, AppointmentUpdate
from autosales.services.appointments import AppointmentService
from autosales.services.notifications import send_telegram

router = APIRouter(prefix="/appointments", tags=["appointments"])


@router.post("", response_model=AppointmentRead, status_code=status.HTTP_201_CREATED)
async def create_appointment(data: AppointmentCreate, session: SessionDep) -> Appointment:
    return await AppointmentService(session).create(data)


@router.get("", response_model=list[AppointmentRead])
async def list_appointments(session: SessionDep, _: StaffDep) -> list[Appointment]:
    return list(
        (await session.scalars(select(Appointment).order_by(Appointment.created_at.desc()))).all()
    )


@router.patch("/{appointment_id}", response_model=AppointmentRead)
async def update_appointment(
    appointment_id: int,
    data: AppointmentUpdate,
    session: SessionDep,
    actor: StaffDep,
    background_tasks: BackgroundTasks,
    settings: SettingsDep,
) -> Appointment:
    appointment = await AppointmentService(session).update(appointment_id, data, actor)
    if data.status is not None or data.appointment_at is not None:
        customer = await session.get(Customer, appointment.customer_id)
        if customer:
            background_tasks.add_task(
                send_telegram,
                settings,
                customer.telegram_id,
                text(
                    "appointment.status_update",
                    normalize_language(customer.language),
                    appointment_id=appointment.id,
                    status=appointment_status_label(appointment.status, customer.language),
                    appointment_at=f"{appointment.appointment_at:%Y-%m-%d %H:%M}",
                ),
            )
    return appointment
