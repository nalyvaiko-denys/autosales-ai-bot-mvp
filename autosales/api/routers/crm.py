from fastapi import APIRouter, BackgroundTasks, Response, status
from sqlalchemy import select

from autosales.ai.content import set_content_status
from autosales.api.deps import SessionDep, SettingsDep, StaffDep
from autosales.i18n import normalize_language, text
from autosales.localization import lead_status_label
from autosales.models import Customer, GeneratedContent, Lead
from autosales.schemas import (
    AnalyticsSummary,
    ContentStatusUpdate,
    GeneratedContentRead,
    LeadCreate,
    LeadRead,
    LeadUpdate,
)
from autosales.services.analytics import analytics_summary
from autosales.services.leads import LeadService
from autosales.services.notifications import send_telegram

router = APIRouter(tags=["crm"])


@router.post("/leads", response_model=LeadRead)
async def create_lead(data: LeadCreate, session: SessionDep, response: Response) -> Lead:
    lead, created = await LeadService(session).create(data)
    response.status_code = status.HTTP_201_CREATED if created else status.HTTP_200_OK
    return lead


@router.get("/leads", response_model=list[LeadRead])
async def list_leads(session: SessionDep, _: StaffDep) -> list[Lead]:
    return list((await session.scalars(select(Lead).order_by(Lead.created_at.desc()))).all())


@router.patch("/leads/{lead_id}", response_model=LeadRead)
async def update_lead(
    lead_id: int,
    data: LeadUpdate,
    session: SessionDep,
    actor: StaffDep,
    background_tasks: BackgroundTasks,
    settings: SettingsDep,
) -> Lead:
    lead = await LeadService(session).update(lead_id, data, actor)
    if data.status is not None:
        customer = await session.get(Customer, lead.customer_id)
        if customer:
            background_tasks.add_task(
                send_telegram,
                settings,
                customer.telegram_id,
                text(
                    "lead.status_update",
                    normalize_language(customer.language),
                    lead_id=lead.id,
                    status=lead_status_label(lead.status, customer.language),
                ),
            )
    return lead


@router.get("/analytics", response_model=AnalyticsSummary)
async def analytics(session: SessionDep, _: StaffDep) -> AnalyticsSummary:
    return await analytics_summary(session)


@router.get("/content", response_model=list[GeneratedContentRead])
async def list_generated_content(session: SessionDep, _: StaffDep) -> list[GeneratedContent]:
    return list(
        (
            await session.scalars(
                select(GeneratedContent).order_by(GeneratedContent.created_at.desc())
            )
        ).all()
    )


@router.patch("/content/{content_id}", response_model=GeneratedContentRead)
async def update_content_status(
    content_id: int,
    data: ContentStatusUpdate,
    session: SessionDep,
    actor: StaffDep,
) -> GeneratedContent:
    return await set_content_status(
        session,
        content_id,
        data.status,
        actor,
        data.approved_by,
    )
