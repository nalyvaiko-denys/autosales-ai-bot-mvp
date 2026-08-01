from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)

from autosales.i18n import button
from autosales.localization import car_status_label

ADMIN_STATS = button("admin.menu.stats", "uk")
ADMIN_INVENTORY = button("admin.menu.inventory", "uk")
ADMIN_CREATE_CAR = button("admin.menu.create_car", "uk")
ADMIN_LEADS = button("admin.menu.leads", "uk")
ADMIN_APPOINTMENTS = button("admin.menu.appointments", "uk")
ADMIN_CONTENT = button("admin.menu.content", "uk")
ADMIN_AI_HELP = button("admin.menu.ai_help", "uk")
ADMIN_EXIT = button("admin.menu.exit", "uk")


def language_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=button("language.uk", "uk")),
                KeyboardButton(text=button("language.en", "en")),
            ]
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def contact_keyboard(language: str = "uk") -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=button("contact.share", language), request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def main_menu(language: str = "uk") -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=button("menu.search", language))],
            [
                KeyboardButton(text=button("menu.catalog", language)),
                KeyboardButton(text=button("menu.favorites", language)),
            ],
            [KeyboardButton(text=button("menu.manager", language))],
        ],
        resize_keyboard=True,
    )


def admin_menu(language: str = "uk") -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=button("admin.menu.inventory", language)),
                KeyboardButton(text=button("admin.menu.create_car", language)),
            ],
            [KeyboardButton(text=button("admin.menu.stats", language))],
            [KeyboardButton(text=button("admin.menu.leads", language))],
            [KeyboardButton(text=button("admin.menu.content", language))],
            [KeyboardButton(text=button("admin.menu.ai_help", language))],
            [KeyboardButton(text=button("admin.menu.exit", language))],
        ],
        resize_keyboard=True,
    )


def photo_upload_keyboard(language: str = "uk") -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=button("admin.publish_done", language))],
            [KeyboardButton(text=button("admin.cancel", language))],
        ],
        resize_keyboard=True,
    )


def admin_car_actions(
    car_id: int, *, archived: bool = False, language: str = "uk"
) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(
                text=button("admin.car.edit", language),
                callback_data=f"admcar:edit:{car_id}",
            ),
            InlineKeyboardButton(
                text=button("admin.car.photos", language),
                callback_data=f"admcar:photos:{car_id}",
            ),
        ],
        [
            InlineKeyboardButton(
                text=button("admin.car.gallery", language),
                callback_data=f"admcar:gallery:{car_id}",
            )
        ],
    ]
    management_row = []
    if not archived:
        management_row.append(
            InlineKeyboardButton(
                text=button("admin.car.archive", language),
                callback_data=f"admcar:archive:{car_id}",
            )
        )
    management_row.append(
        InlineKeyboardButton(
            text=button("admin.car.delete", language),
            callback_data=f"admcar:delete:{car_id}",
        )
    )
    rows.append(management_row)
    return InlineKeyboardMarkup(inline_keyboard=rows)


def admin_car_edit_fields(car_id: int, language: str = "uk") -> InlineKeyboardMarkup:
    fields = [
        (button("admin.field.name", language), "name"),
        (button("admin.field.year", language), "year"),
        (button("admin.field.price", language), "price"),
        (button("admin.field.fuel", language), "fuel_type"),
        (button("admin.field.transmission", language), "transmission"),
        (button("admin.field.engine", language), "engine"),
        (button("admin.field.drive", language), "drive_type"),
        (button("admin.field.body", language), "body_type"),
        (button("admin.field.status", language), "status"),
        (button("admin.field.location", language), "location_id"),
    ]
    rows = [
        [
            InlineKeyboardButton(text=label, callback_data=f"admcar:field:{car_id}:{field}")
            for label, field in fields[index : index + 2]
        ]
        for index in range(0, len(fields), 2)
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def admin_car_statuses(car_id: int, *, action: str, language: str = "uk") -> InlineKeyboardMarkup:
    statuses = [
        (car_status_label("available", language), "available"),
        (car_status_label("reserved", language), "reserved"),
        (car_status_label("sold", language), "sold"),
        (car_status_label("archived", language), "archived"),
    ]
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=label,
                    callback_data=f"admcar:{action}:{car_id}:{status}",
                )
                for label, status in statuses[index : index + 2]
            ]
            for index in range(0, len(statuses), 2)
        ]
    )


def admin_locations(locations: list[tuple[int, str]], *, action: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=name, callback_data=f"admcar:{action}:{location_id}")]
            for location_id, name in locations
        ]
    )


def admin_inventory_locations(
    locations: list[tuple[int, str]], language: str = "uk"
) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(
                text=button("admin.inventory.all_locations", language),
                callback_data="admcar:listloc:all",
            )
        ]
    ]
    rows.extend(
        [InlineKeyboardButton(text=name, callback_data=f"admcar:listloc:{location_id}")]
        for location_id, name in locations
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def admin_photo_actions(
    car_id: int, media: list[tuple[int, bool]], language: str = "uk"
) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(
                text=button("admin.car.add_photo", language),
                callback_data=f"admcar:addphotos:{car_id}",
            )
        ]
    ]
    for index in range(0, len(media), 3):
        rows.append(
            [
                InlineKeyboardButton(
                    text=(
                        f"{'⭐ ' if is_main else ''}"
                        f"{button('admin.car.cover', language).format(position=position)}"
                    ),
                    callback_data=f"admcar:cover:{car_id}:{media_id}",
                )
                for position, (media_id, is_main) in enumerate(
                    media[index : index + 3], start=index + 1
                )
            ]
        )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def archive_confirmation(car_id: int, language: str = "uk") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=button("admin.confirm.archive", language),
                    callback_data=f"admcar:archok:{car_id}",
                ),
                InlineKeyboardButton(
                    text=button("admin.cancel", language),
                    callback_data=f"admcar:archno:{car_id}",
                ),
            ]
        ]
    )


def car_delete_confirmation(car_id: int, language: str = "uk") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=button("admin.confirm.delete", language),
                    callback_data=f"admcar:delok:{car_id}",
                ),
                InlineKeyboardButton(
                    text=button("admin.cancel", language),
                    callback_data=f"admcar:delno:{car_id}",
                ),
            ]
        ]
    )


def lead_contact_action(lead_id: int, language: str = "uk") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=button("admin.action.contact", language),
                    callback_data=f"adm:lead:{lead_id}:contact",
                )
            ]
        ]
    )


def admin_lead_actions(
    lead_id: int, *, can_contact: bool, language: str = "uk"
) -> InlineKeyboardMarkup:
    rows = []
    if can_contact:
        rows.append(
            [
                InlineKeyboardButton(
                    text=button("admin.action.contact", language),
                    callback_data=f"adm:lead:{lead_id}:contact",
                )
            ]
        )
    rows.append(
        [
            InlineKeyboardButton(
                text=button("admin.action.edit", language),
                callback_data=f"adm:lead:{lead_id}:edit",
            )
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def admin_lead_edit_actions(lead_id: int, language: str = "uk") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=button("admin.action.delete_lead", language),
                    callback_data=f"adm:lead:{lead_id}:delete",
                )
            ],
            [
                InlineKeyboardButton(
                    text=button("admin.action.back", language),
                    callback_data=f"adm:lead:{lead_id}:back",
                )
            ],
        ]
    )


def admin_lead_delete_confirmation(lead_id: int, language: str = "uk") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=button("admin.confirm.delete", language),
                    callback_data=f"adm:lead:{lead_id}:delete_confirm",
                ),
                InlineKeyboardButton(
                    text=button("admin.cancel", language),
                    callback_data=f"adm:lead:{lead_id}:back",
                ),
            ]
        ]
    )


def admin_appointment_actions(
    appointment_id: int, *, can_contact: bool, language: str = "uk"
) -> InlineKeyboardMarkup:
    rows = []
    if can_contact:
        rows.append(
            [
                InlineKeyboardButton(
                    text=button("admin.action.contact", language),
                    callback_data=f"adm:appointment:{appointment_id}:contact",
                )
            ]
        )
    rows.append(
        [
            InlineKeyboardButton(
                text=button("admin.action.edit", language),
                callback_data=f"adm:appointment:{appointment_id}:edit",
            )
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def admin_appointment_edit_actions(
    appointment_id: int, language: str = "uk"
) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=button("admin.action.delete_appointment", language),
                    callback_data=f"adm:appointment:{appointment_id}:delete",
                )
            ],
            [
                InlineKeyboardButton(
                    text=button("admin.action.back", language),
                    callback_data=f"adm:appointment:{appointment_id}:back",
                )
            ],
        ]
    )


def admin_appointment_delete_confirmation(
    appointment_id: int, language: str = "uk"
) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=button("admin.confirm.delete", language),
                    callback_data=f"adm:appointment:{appointment_id}:delete_confirm",
                ),
                InlineKeyboardButton(
                    text=button("admin.cancel", language),
                    callback_data=f"adm:appointment:{appointment_id}:back",
                ),
            ]
        ]
    )


def admin_content_actions(content_id: int, language: str = "uk") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=button("admin.action.approve", language),
                    callback_data=f"adm:content:{content_id}:approved",
                ),
                InlineKeyboardButton(
                    text=button("admin.action.reject", language),
                    callback_data=f"adm:content:{content_id}:rejected",
                ),
            ]
        ]
    )


def car_actions(
    car_id: int, *, is_favorite: bool = False, language: str = "uk"
) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(
                text=button("car.gallery", language), callback_data=f"gallery:{car_id}"
            )
        ],
        [
            InlineKeyboardButton(
                text=button("car.favorite_remove" if is_favorite else "car.favorite_add", language),
                callback_data=f"unfav:{car_id}" if is_favorite else f"fav:{car_id}",
            )
        ],
        [
            InlineKeyboardButton(
                text=button("car.manager", language), callback_data=f"lead:{car_id}"
            )
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def catalog_navigation(page: int, pages: int, language: str = "uk") -> InlineKeyboardMarkup:
    navigation = []
    if page > 1:
        navigation.append(
            InlineKeyboardButton(
                text=button("navigation.previous", language),
                callback_data=f"catalog:{page - 1}",
            )
        )
    navigation.append(InlineKeyboardButton(text=f"{page}/{pages}", callback_data="noop"))
    if page < pages:
        navigation.append(
            InlineKeyboardButton(
                text=button("navigation.next", language),
                callback_data=f"catalog:{page + 1}",
            )
        )
    return InlineKeyboardMarkup(inline_keyboard=[navigation])
