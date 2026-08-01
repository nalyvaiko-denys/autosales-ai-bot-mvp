import secrets
from typing import Any

from fastapi import FastAPI, Request
from sqladmin import Admin, ModelView
from sqladmin.authentication import AuthenticationBackend
from sqlalchemy.ext.asyncio import AsyncEngine

from autosales.config import Settings
from autosales.localization import (
    appointment_status_label,
    car_status_label,
    content_status_label,
    lead_status_label,
)
from autosales.models import (
    Appointment,
    AuditLog,
    Car,
    Customer,
    GeneratedContent,
    KnowledgeDocument,
    Lead,
    Location,
    Manager,
)
from autosales.services.inventory import delete_car


class AuditedModelView:
    """Write every SQLAdmin mutation to AuditLog in a separate transaction."""

    async def after_model_change(
        self, data: dict[str, Any], model: Any, is_created: bool, request: Request
    ) -> None:
        values = {key: str(value) if value is not None else None for key, value in data.items()}
        async with self.session_maker(expire_on_commit=False) as session:
            session.add(
                AuditLog(
                    user_id=f"admin:{request.session.get('staff', 'unknown')}",
                    action="admin.create" if is_created else "admin.update",
                    entity_type=model.__class__.__name__.lower(),
                    entity_id=str(model.id),
                    old_value=None,
                    new_value=values,
                )
            )
            await session.commit()

    async def after_model_delete(self, model: Any, request: Request) -> None:
        async with self.session_maker(expire_on_commit=False) as session:
            session.add(
                AuditLog(
                    user_id=f"admin:{request.session.get('staff', 'unknown')}",
                    action="admin.delete",
                    entity_type=model.__class__.__name__.lower(),
                    entity_id=str(model.id),
                )
            )
            await session.commit()


class StaffAuthentication(AuthenticationBackend):
    def __init__(self, settings: Settings):
        super().__init__(secret_key=settings.session_secret.get_secret_value())
        self.username = settings.admin_username
        self.password = settings.admin_password.get_secret_value()

    async def login(self, request: Request) -> bool:
        form = await request.form()
        username = str(form.get("username", ""))
        password = str(form.get("password", ""))
        valid = secrets.compare_digest(username, self.username) and secrets.compare_digest(
            password, self.password
        )
        if valid:
            request.session.update({"staff": username})
        return valid

    async def logout(self, request: Request) -> bool:
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> bool:
        return request.session.get("staff") == self.username


class LocationAdmin(AuditedModelView, ModelView, model=Location):
    name_plural = "Майданчики"
    column_list = [Location.id, Location.name, Location.city, Location.address, Location.is_active]
    column_searchable_list = [Location.name, Location.city, Location.address]


class CarAdmin(AuditedModelView, ModelView, model=Car):
    name_plural = "Автомобілі"
    column_list = [
        Car.id,
        Car.brand,
        Car.model,
        Car.year,
        Car.price,
        Car.status,
        Car.location_id,
        Car.updated_at,
    ]
    column_searchable_list = [Car.brand, Car.model, Car.vin]
    column_filters = [Car.status, Car.location_id, Car.brand, Car.year]
    column_default_sort = [(Car.updated_at, True)]
    column_formatters = {Car.status: lambda model, attribute: car_status_label(model.status)}
    can_delete = True

    async def delete_model(self, request: Request, pk: Any) -> None:
        async with self.session_maker(expire_on_commit=False) as session:
            await delete_car(
                session,
                int(pk),
                actor=f"admin:{request.session.get('staff', 'unknown')}",
            )


class CustomerAdmin(AuditedModelView, ModelView, model=Customer):
    name_plural = "Клієнти"
    can_create = False
    column_list = [
        Customer.id,
        Customer.first_name,
        Customer.phone,
        Customer.telegram_id,
        Customer.last_activity_at,
    ]
    column_searchable_list = [Customer.first_name, Customer.phone, Customer.username]


class ManagerAdmin(AuditedModelView, ModelView, model=Manager):
    name_plural = "Менеджери"
    column_list = [Manager.id, Manager.name, Manager.role, Manager.location_id, Manager.is_active]


class LeadAdmin(AuditedModelView, ModelView, model=Lead):
    name_plural = "Заявки"
    column_list = [
        Lead.id,
        Lead.customer_id,
        Lead.car_id,
        Lead.manager_id,
        Lead.status,
        Lead.priority,
        Lead.next_contact_at,
        Lead.created_at,
    ]
    column_filters = [Lead.status, Lead.priority, Lead.manager_id]
    column_formatters = {Lead.status: lambda model, attribute: lead_status_label(model.status)}
    can_delete = False


class AppointmentAdmin(AuditedModelView, ModelView, model=Appointment):
    name_plural = "Записи"
    column_list = [
        Appointment.id,
        Appointment.customer_id,
        Appointment.car_id,
        Appointment.appointment_at,
        Appointment.status,
        Appointment.manager_id,
    ]
    column_filters = [Appointment.status, Appointment.location_id]
    column_formatters = {
        Appointment.status: lambda model, attribute: appointment_status_label(model.status)
    }


class KnowledgeAdmin(AuditedModelView, ModelView, model=KnowledgeDocument):
    name_plural = "База знань"
    column_list = [
        KnowledgeDocument.id,
        KnowledgeDocument.title,
        KnowledgeDocument.document_type,
        KnowledgeDocument.is_active,
        KnowledgeDocument.updated_at,
    ]


class GeneratedContentAdmin(AuditedModelView, ModelView, model=GeneratedContent):
    name_plural = "Згенерований контент"
    column_list = [
        GeneratedContent.id,
        GeneratedContent.car_id,
        GeneratedContent.content_type,
        GeneratedContent.status,
        GeneratedContent.generated_by,
        GeneratedContent.created_at,
    ]
    column_filters = [GeneratedContent.status, GeneratedContent.content_type]
    column_formatters = {
        GeneratedContent.status: lambda model, attribute: content_status_label(model.status)
    }
    can_create = False
    can_delete = False


class AuditAdmin(ModelView, model=AuditLog):
    name_plural = "Журнал змін"
    column_list = [
        AuditLog.id,
        AuditLog.user_id,
        AuditLog.action,
        AuditLog.entity_type,
        AuditLog.entity_id,
        AuditLog.created_at,
    ]
    can_create = False
    can_edit = False
    can_delete = False


def mount_admin(app: FastAPI, db_engine: AsyncEngine, settings: Settings) -> Admin:
    admin = Admin(
        app,
        db_engine,
        title="AutoSales CRM",
        base_url="/admin",
        authentication_backend=StaffAuthentication(settings),
    )
    for view in (
        LocationAdmin,
        CarAdmin,
        CustomerAdmin,
        ManagerAdmin,
        LeadAdmin,
        AppointmentAdmin,
        KnowledgeAdmin,
        GeneratedContentAdmin,
        AuditAdmin,
    ):
        admin.add_view(view)
    return admin
