"""Ukrainian language resources.

The persisted ISO 639-1 language code is ``uk``.  The module is named ``ua``
because that is the familiar language selector name for the business.
"""

LANGUAGE = "uk"

BUTTONS = {
    "language.uk": "Українська",
    "language.en": "English",
    "contact.share": "📱 Надіслати номер",
    "menu.search": "🔎 Знайти авто",
    "menu.catalog": "🚘 Каталог",
    "menu.favorites": "⭐ Обране",
    "menu.manager": "💬 Написати менеджеру",
    "menu.ai_search": "✨ AI-підбір",
    "menu.ai_assistant": "🤖 AI-асистент",
    "menu.my_leads": "📋 Мої заявки",
    "menu.question": "❓ Поставити запитання",
    "menu.manager_legacy": "👤 Зв’язатися з менеджером",
    "car.gallery": "🖼 Відкрити галерею",
    "car.favorite_add": "⭐ В обране",
    "car.favorite_remove": "❌ Прибрати з обраного",
    "car.manager": "💬 Запитати менеджера",
    "navigation.previous": "← Попередня",
    "navigation.next": "Наступна →",
    "admin.menu.stats": "📊 Статистика",
    "admin.menu.inventory": "🚗 База автомобілів",
    "admin.menu.create_car": "➕ Додати автомобіль",
    "admin.menu.leads": "📥 Звернення клієнтів",
    "admin.menu.appointments": "📅 Записи на перегляд",
    "admin.menu.content": "📝 Чернетки контенту",
    "admin.menu.ai_help": "🧠 Як працює LangGraph",
    "admin.menu.exit": "↩️ Вийти з адмін-режиму",
    "admin.publish_done": "✅ Завершити публікацію",
    "admin.cancel": "❌ Скасувати",
    "admin.photo_done": "✅ Фото завантажено",
    "admin.car.edit": "✏️ Редагувати",
    "admin.car.photos": "📷 Фото",
    "admin.car.gallery": "🖼 Галерея",
    "admin.car.archive": "🗄 Архівувати",
    "admin.car.delete": "🗑 Видалити",
    "admin.inventory.all_locations": "Усі майданчики",
    "admin.car.add_photo": "➕ Додати фото",
    "admin.car.cover": "Обкладинка #{position}",
    "admin.field.name": "Назва авто",
    "admin.field.year": "Рік",
    "admin.field.price": "Ціна",
    "admin.field.fuel": "Паливо",
    "admin.field.transmission": "Коробка",
    "admin.field.engine": "Двигун / потужність",
    "admin.field.drive": "Привід",
    "admin.field.body": "Тип кузова",
    "admin.field.status": "Статус",
    "admin.field.location": "Адреса",
    "admin.confirm.archive": "Так, архівувати",
    "admin.confirm.delete": "Так, видалити",
    "admin.action.contact": "📞 Зв’язатись",
    "admin.action.edit": "✏️ Редагувати",
    "admin.action.delete_lead": "🗑 Видалити звернення",
    "admin.action.delete_appointment": "🗑 Видалити запис",
    "admin.action.back": "← Назад",
    "admin.action.approve": "✅ Схвалити",
    "admin.action.reject": "❌ Відхилити",
}

TEXTS = {
    "language.choose": "Оберіть мову / Choose language",
    "welcome": "Вітаємо, {name}!",
    "registration.ask_name": "Як до вас звертатися?",
    "registration.ask_contact": "Надішліть номер телефону через кнопку Telegram.",
    "registration.own_contact": "Будь ласка, надішліть власний контакт кнопкою нижче.",
    "registration.completed": "Реєстрацію завершено ✅",
    "language.changed": "Мову змінено ✅",
    "start.required": "Спочатку виконайте /start",
    "start.registration_required": "Спочатку завершіть реєстрацію через /start.",
    "car.address": "Адреса",
    "car.liter": "л",
    "car.kilowatt": "кВт",
    "car.kilometer": "км",
    "car.finance": "Можливий продаж в кредит або лізинг",
    "catalog.error": "Сталася помилка при завантаженні каталогу. Спробуйте ще раз.",
    "catalog.empty": "У каталозі поки немає доступних автомобілів.",
    "catalog.heading": "🚘 <b>Каталог · сторінка {page}/{pages}</b>",
    "catalog.count": "Автомобілів: {total}. На сторінці: {count}.",
    "catalog.render_error": "Сталася помилка при відображенні автомобілів. Спробуйте ще раз.",
    "catalog.navigation": "Перейдіть до іншої сторінки:",
    "catalog.busy": "Каталог уже завантажується, зачекайте кілька секунд.",
    "catalog.page_busy": "Сторінка вже завантажується",
    "catalog.loading": "Завантажую сторінку…",
    "search.prompt": (
        "Напишіть один або декілька критеріїв звичайним текстом. Наприклад: "
        "«Toyota», «до 15000$», «від 2018 року» або повний опис авто."
    ),
    "search.ai_prompt": (
        "Опишіть бажане авто звичайними словами: марка, кузов, бюджет, рік, пробіг, "
        "паливо, коробка або привід."
    ),
    "assistant.prompt": (
        "Напишіть звичайний опис без спеціального формату. Наприклад: «Мазда 3, "
        "пробіг до 100000, ціна до 9890$, 1.4 бензин, автомат, від 2011 року»."
    ),
    "search.refinement": "Уточнення користувача: {text}",
    "search.processing": "Опрацьовую запит…",
    "search.failed": "Не вдалося опрацювати запит. Спробуйте уточнити його.",
    "search.clarify_numbers": "Уточніть числові параметри.",
    "search.not_found": "За вашим запитом нічого не знайдено.",
    "search.found": "Знайдено автомобілів: {count}. Показую результати:",
    "search.why": "Чому підходить:",
    "search.match": "Відповідність: {score}",
    "search.error": "Сталася помилка при пошуку. Спробуйте ще раз трохи пізніше.",
    "search.error_code": "Код помилки: <code>{error_id}</code>",
    "search.ambiguous": (
        "Уточніть, що означає {values}: ціна, рік чи пробіг. Наприклад: "
        "«ціна 5000 EUR, рік від 1998, пробіг до 150 000 км». "
        "Коми, крапки й дефіси не обов’язкові."
    ),
    "search.no_candidates": (
        "За обов’язковими критеріями немає доступних авто. "
        "Уточніть, який параметр можна змінити, але бюджет не буде перевищено."
    ),
    "search.objective_only": (
        "Вкажіть хоча б один об’єктивний критерій: марку, модель, ціну, рік, пробіг, "
        "паливо, коробку, привід або кузов. Оцінки на кшталт «надійна» чи «економна» не "
        "використовуються для пошуку."
    ),
    "favorite.added": "Додано в обране ⭐",
    "favorite.removed": "Прибрано з обраного",
    "favorite.empty": "В обраному поки порожньо.",
    "gallery.unavailable": "Автомобіль більше недоступний",
    "gallery.empty": "Для цього авто фотографій ще немає",
    "lead.request_message": "Клієнт просить зв’язатися щодо автомобіля",
    "lead.transferred": "Запит передано менеджеру",
    "lead.thanks": ("Дякуємо. Менеджер отримав ваш запит щодо цього авто і зв’яжеться з вами."),
    "lead.error": "Не вдалося передати запит менеджеру. Спробуйте ще раз.",
    "lead.error_code": "Код помилки: <code>{error_id}</code>",
    "lead.manager_claimed": "Менеджер уже отримав ваше звернення та зв’яжеться з вами.",
    "appointment.ask_date": (
        "Введіть бажані дату й час у форматі <code>2026-08-15 14:30</code>. "
        "Менеджер підтвердить час вручну."
    ),
    "appointment.invalid_date": "Не вдалося розпізнати дату. Приклад: 2026-08-15 14:30",
    "appointment.created": (
        "Запит на перегляд #{appointment_id} створено. Очікуйте підтвердження менеджера."
    ),
    "appointment.manager_claimed": (
        "Менеджер уже отримав ваш запит на перегляд та зв’яжеться з вами."
    ),
    "appointment.reminder": (
        "Нагадування: перегляд авто #{car_id} заплановано на {appointment_at}."
    ),
    "appointment.status_update": "Запис #{appointment_id}: {status}, {appointment_at}.",
    "leads.empty": "У вас ще немає заявок.",
    "leads.item": "#{lead_id} · {status} · авто {car}",
    "leads.no_car": "не вибрано",
    "lead.status_update": "Стан вашого звернення #{lead_id}: {status}.",
    "question.prompt": "Напишіть запитання про купівлю, резервування або майданчики.",
    "manager.prompt": "Коротко опишіть ваше питання — його отримає менеджер.",
    "manager.thanks": "Дякуємо. Менеджер отримав повідомлення та зв’яжеться з вами.",
    "explanation.price": "ціна {price} {currency} у межах бюджету",
    "explanation.year": "{year} рік",
    "explanation.mileage": "пробіг {mileage} км",
    "explanation.engine": "двигун {volume} л",
    "explanation.power": "потужність {power} кВт",
    "explanation.transmission": "коробка {transmission}",
    "explanation.fuel": "паливо {fuel}",
    "explanation.body": "кузов {body}",
    "explanation.drive": "привід {drive}",
    "rag.missing": "Ця характеристика не вказана. Передам запит менеджеру для уточнення.",
    "content.manager_details": "Деталі та актуальну наявність уточнюйте у менеджера.",
    "content.phones": "Телефони: {phones}.",
    "content.price": "Ціна: {price} {currency}.",
    "content.fuel": "Паливо: {fuel}.",
    "content.transmission": "Коробка: {transmission}.",
    "content.drive": "Привід: {drive}.",
    "content.mileage": "Пробіг: {mileage} км.",
    "fuel.petrol": "бензин",
    "fuel.diesel": "дизель",
    "fuel.gas": "газ/бензин",
    "fuel.hybrid": "гібрид",
    "fuel.electric": "електро",
    "transmission.automatic": "автомат",
    "transmission.manual": "механіка",
    "drive.awd": "повний привід",
    "drive.fwd": "передній привід",
    "drive.rwd": "задній привід",
    "drive.not_specified": "не вказано",
    "body.crossover": "кросовер",
    "body.suv": "позашляховик",
    "body.sedan": "седан",
    "body.hatchback": "хетчбек",
    "body.wagon": "універсал",
    "body.minivan": "мінівен / компактвен",
    "body.coupe": "купе",
    "body.liftback": "ліфтбек",
    "body.convertible": "кабріолет / родстер",
    "body.pickup": "пікап",
    "body.van": "мікроавтобус / фургон",
    "body.not_specified": "не вказано",
    "car_status.available": "в наявності",
    "car_status.reserved": "резерв",
    "car_status.sold": "продано",
    "car_status.archived": "архів",
    "lead_status.new": "нове",
    "lead_status.in_progress": "в роботі",
    "lead_status.contacted": "менеджер зв’язується",
    "lead_status.appointment_scheduled": "перегляд заплановано",
    "lead_status.test_drive_completed": "тест-драйв завершено",
    "lead_status.reserved": "зарезервовано",
    "lead_status.won": "успішно завершено",
    "lead_status.lost": "закрито",
    "lead_status.spam": "неактуальне",
    "content_status.draft": "чернетка",
    "content_status.approved": "схвалено",
    "content_status.rejected": "відхилено",
    "content_status.published": "опубліковано",
    "appointment_status.pending": "очікує менеджера",
    "appointment_status.confirmed": "підтверджено",
    "appointment_status.completed": "завершено",
    "appointment_status.cancelled": "скасовано",
    "currency.USD": "дол. США",
    "currency.EUR": "євро",
    "currency.UAH": "грн",
    "command.start": "Головне меню",
    "command.ai": "AI-асистент LangGraph",
    "command.id": "Показати мій Telegram ID",
    "command.admin": "Telegram-адмінка",
    "command.language": "Змінити мову",
    "admin.state.waiting": "очікує менеджера",
    "admin.state.claimed": "менеджер уже зв’язується",
    "admin.no_car": "без авто",
    "admin.not_specified": "не вказано",
    "admin.unknown_user": "невідомий",
    "admin.lead.card": (
        "📥 <b>Звернення #{lead_id}</b>\n"
        "Стан: {state}\n"
        "Клієнт: {customer}\n"
        "Телефон: <code>{phone}</code>\n"
        "Авто: {car}\n"
        "Повідомлення: {message}"
    ),
    "admin.appointment.card": (
        "📅 <b>Звернення на перегляд #{appointment_id}</b>\n"
        "Стан: {state}\n"
        "Бажаний час: {appointment_at}\n"
        "Клієнт: {customer}\n"
        "Телефон: <code>{phone}</code>\n"
        "Авто: {car}"
    ),
    "admin.access_denied": (
        "⛔️ Немає доступу до Telegram-адмінки.\n"
        "Ваш Telegram ID: <code>{user_id}</code>\n"
        "Додайте його до <code>TELEGRAM_ADMIN_IDS</code> у .env і перезапустіть bot."
    ),
    "admin.access_denied_short": "Немає доступу",
    "admin.access_denied_inventory": ("⛔️ Немає доступу. Додайте свій ID у TELEGRAM_ADMIN_IDS."),
    "admin.telegram_id": "Ваш Telegram ID: <code>{user_id}</code>",
    "admin.enter": "🔐 <b>Telegram-адмінка</b>\nОберіть розділ:",
    "admin.closed": "Адмін-режим закрито.",
    "admin.stats": (
        "📊 <b>Статистика</b>\n"
        "Клієнти: {customers}\n"
        "Заявки: {leads}\n"
        "Записи: {appointments}\n"
        "Авто в наявності: {available_cars}\n"
        "Продано: {sold_cars}\n"
        "Конверсія заявка → запис: {lead_conversion}\n"
        "Конверсія запис → продаж: {sale_conversion}"
    ),
    "admin.leads.empty": "Звернень клієнтів поки немає.",
    "admin.leads.heading": "📥 <b>Останні звернення та записи на перегляд</b>",
    "admin.content.empty": "Чернеток на погодження немає.",
    "admin.content.card": (
        "📝 <b>Контент #{content_id}</b> · {content_type}\nАвто: {car}\n\n{content}"
    ),
    "admin.ai_help": (
        "🧠 <b>LangGraph у цьому боті</b>\n\n"
        "Кнопка <b>🤖 AI-асистент</b> або команда /ai запускає граф:\n"
        "<code>classify → search | knowledge</code>\n\n"
        "• пошук авто: «Які автомобілі Audi є зараз у наявності?»;\n"
        "• база знань: «Які документи потрібні для тест-драйву?».\n\n"
        "LangGraph керує маршрутом і станом. LangChain окремо не потрібен: "
        "граф уже використовує langchain-core, а SQL-фільтри та RAG залишаються "
        "контрольованими."
    ),
    "admin.inventory.module_missing": (
        "Перезапустіть bot: модуль управління авто ще не підключився."
    ),
    "admin.confirm_delete": "Підтвердьте видалення",
    "admin.lead.deleted_message": "🗑 Звернення #{lead_id} видалено.",
    "admin.lead.deleted": "Звернення видалено",
    "admin.lead.already_deleted": "Звернення вже видалено",
    "admin.lead.already_claimed": "Це звернення вже взяв інший менеджер",
    "admin.lead.claimed": "Звернення взято. Можна телефонувати клієнту.",
    "admin.appointment.deleted_message": "🗑 Запис #{appointment_id} видалено.",
    "admin.appointment.deleted": "Запис видалено",
    "admin.appointment.already_deleted": "Запис уже видалено",
    "admin.appointment.already_claimed": "Цей запис уже взяв інший менеджер",
    "admin.appointment.claimed": "Запис взято. Можна телефонувати клієнту.",
    "admin.unknown_action": "Невідома дія",
    "admin.operation_failed": "Не вдалося виконати дію. Оновіть розділ і спробуйте ще раз.",
    "admin.invalid_status": "Недопустимий статус",
    "admin.content.updated": "Контент #{content_id}: {status}",
    "admin.inventory.empty": "База автомобілів поки порожня.",
    "admin.inventory.heading": "Останні авто в усіх статусах:",
    "admin.inventory.filter_choose": "Оберіть майданчик, автомобілі якого потрібно показати:",
    "admin.inventory.loading_location": "Завантажую автомобілі майданчика…",
    "admin.inventory.empty_for_location": "На майданчику «{location}» автомобілів немає.",
    "admin.inventory.heading_filtered": ("🚗 <b>{location}</b>\nЗнайдено автомобілів: {count}"),
    "admin.inventory.cancelled": "Дію скасовано.",
    "admin.inventory.unrecognized": "не розпізнано",
    "admin.inventory.recognized": (
        "<b>Розпізнано з опису:</b>\n"
        "Авто: {name}\n"
        "Рік: {year}\n"
        "Коробка: {transmission}\n"
        "Двигун: {engine}\n"
        "Паливо: {fuel}\n"
        "Привід: {drive}\n"
        "Кузов: {body}\n"
        "Ціна: {price} {currency}\n"
        "Пробіг: {mileage} км"
    ),
    "admin.inventory.card": (
        "<b>#{car_id} · {brand} {model} · {year}</b>\n"
        "💵 {price} {currency}\n"
        "⚙️ {details}\n"
        "📍 Адреса: {location}\n"
        "Статус: <b>{status}</b>{mileage}"
    ),
    "admin.inventory.card_mileage": "\nПробіг: {mileage} км",
    "admin.inventory.prompt.name": (
        "Введіть назву автомобіля: марка та модель, наприклад Mazda 3:"
    ),
    "admin.inventory.prompt.year": "Введіть рік випуску, наприклад 2021:",
    "admin.inventory.prompt.price": "Введіть ціну, наприклад 18500$:",
    "admin.inventory.prompt.fuel_type": (
        "Введіть паливо: бензин, дизель, газ/бензин, гібрид або електро:"
    ),
    "admin.inventory.prompt.transmission": "Введіть коробку: автомат або механіка:",
    "admin.inventory.prompt.engine_volume": ("Введіть об’єм двигуна, наприклад 1.4 або 2.0:"),
    "admin.inventory.prompt.engine_power": "Введіть потужність електромобіля, наприклад 150 кВт:",
    "admin.inventory.prompt.drive_type": "Введіть привід: передній, задній або повний:",
    "admin.inventory.prompt.body_type": (
        "Введіть тип кузова: седан, хетчбек, універсал, ліфтбек, кросовер, "
        "позашляховик, купе, кабріолет/родстер, мінівен/компактвен, пікап або "
        "мікроавтобус/фургон:"
    ),
    "admin.inventory.location_missing": ("Немає активних майданчиків. Додайте адресу у веб-CRM."),
    "admin.inventory.location_choose": "Оберіть адресу майданчика:",
    "admin.inventory.create_failed": "Не вдалося створити чернетку: {error}",
    "admin.inventory.draft_created": (
        "Чернетку #{car_id} створено. Надішліть до {max_photos} фото одним "
        "альбомом або окремо. Перше фото стане обкладинкою."
    ),
    "admin.inventory.create_intro": (
        "Надішліть один звичайний опис автомобіля. Я сам заповню пост і запитаю "
        "лише те, чого справді не вистачає.\n\n"
        "Приклад: <code>Мазда 3, пробіг 10000, ціна 9890$, 1.4 бензин, "
        "автомат, передній привід, седан, 2011 рік, механізаторів</code>\n\n"
        "Адреса 1 — Київське шосе, 41А; адреса 2 — Механізаторів, 1А."
    ),
    "admin.inventory.recognizing": "Розпізнаю дані автомобіля…",
    "admin.inventory.error.name": "Вкажіть і марку, і модель. Наприклад: Mazda 3.",
    "admin.inventory.error.year": "Рік має бути числом від 1900 до 2100.",
    "admin.inventory.error.transmission": "Напишіть «автомат» або «механіка».",
    "admin.inventory.error.engine": ("Введіть об’єм числом, наприклад 1.4 або 2.0."),
    "admin.inventory.error.engine_power": "Введіть потужність від 1 до 2000 кВт.",
    "admin.inventory.error.fuel": (
        "Вкажіть бензин, дизель, газ/бензин, гібрид або електро."
    ),
    "admin.inventory.error.drive_type": "Вкажіть передній, задній або повний привід.",
    "admin.inventory.error.body_type": "Вкажіть один із запропонованих типів кузова.",
    "admin.inventory.error.price": ("Введіть додатну ціну, наприклад 9890$ або 9200 EUR."),
    "admin.inventory.photo_added_count": "Фото додано. Усього: {count}.",
    "admin.inventory.photo_required": "Додайте щонайменше одну фотографію.",
    "admin.inventory.saved": "Автомобіль #{car_id} збережено, фото: {photo_count} ✅",
    "admin.inventory.edit_choose": "Що змінити в авто #{car_id}?",
    "admin.inventory.status_choose": "Оберіть новий статус:",
    "admin.inventory.location_new_choose": "Оберіть новий майданчик:",
    "admin.inventory.invalid_value": "Некоректне значення: {error}",
    "admin.inventory.updated": "Авто #{car_id} оновлено ✅",
    "admin.inventory.status_updated": "Новий статус: {status}",
    "admin.inventory.location_updated": "Майданчик авто #{car_id} змінено",
    "admin.inventory.location_updated_to": (
        "Авто #{car_id} переміщено до «{location}» ✅ Базу автомобілів оновлено."
    ),
    "admin.inventory.photos": (
        "Фото авто #{car_id}: {count}. Натисніть номер, щоб зробити його обкладинкою."
    ),
    "admin.inventory.photos_add": (
        "Надішліть додаткові фото окремо або одним альбомом. Потім натисніть кнопку нижче."
    ),
    "admin.inventory.photo_added": "Фото додано.",
    "admin.inventory.photos_saved": "Фотографії збережено ✅",
    "admin.inventory.cover_changed": "Обкладинку змінено ⭐",
    "admin.inventory.photos_empty": "У цього авто ще немає фотографій",
    "admin.inventory.archive_confirm": (
        "Авто зникне з клієнтського каталогу, але залишиться в базі й його можна "
        "буде відновити зміною статусу. Продовжити?"
    ),
    "admin.inventory.archived": "Авто #{car_id} перенесено в архів",
    "admin.inventory.archive_cancelled": "Архівування скасовано",
    "admin.inventory.delete_confirm": (
        "⚠️ Це повністю видалить пост, його фото та пов’язані записи публікації з бази. "
        "Дію неможливо скасувати."
    ),
    "admin.inventory.deleted": "Авто #{car_id} повністю видалено",
    "admin.inventory.already_deleted": "Це авто вже видалено",
    "admin.inventory.delete_cancelled": "Видалення скасовано",
}

PROMPTS = {
    "criteria.system": (
        "Витягни критерії пошуку автомобіля з українського або англійського тексту. "
        "Нормалізуй тип кузова до sedan/hatchback/wagon/liftback/crossover/suv/coupe/"
        "convertible/minivan/pickup/van, паливо до petrol/diesel/gas/hybrid/electric, "
        "коробку до automatic/manual, привід до fwd/rwd/awd. Код gas означає "
        "газ/бензин. Враховуй друкарські помилки, дефіси, подвоєні літери й англійські "
        "назви кузовів. Витягни лише явно названі марку, модель, валюту, об’єм двигуна "
        "або потужність у кВт. Пунктуація "
        "й порядок слів не мають значення. Не визначай навмання, чи число без підпису "
        "є ціною, роком або пробігом. Числові верхні межі є жорсткими. Не витягуй і не "
        "вгадуй колір: зовнішність не є структурованим параметром каталогу. Не перетворюй "
        "слова «надійна», «економна», «перша машина», «сімейна», «комфортна» чи подібні "
        "суб’єктивні оцінки на критерії пошуку. Не додавай жодних фактів, яких користувач "
        "не вказав."
    ),
    "car_draft.system": (
        "Перетвори довільний український або англійський опис оголошення на структуровані "
        "поля: марка, модель, рік, коробка, об’єм двигуна або потужність у кВт, паливо, "
        "ціна, валюта, пробіг, кузов і привід. Нормалізуй кузов до sedan/hatchback/wagon/"
        "liftback/crossover/suv/coupe/convertible/minivan/pickup/van, коробку до "
        "automatic/manual, паливо до petrol/diesel/gas/hybrid/electric, привід до "
        "fwd/rwd/awd. Код gas означає газ/бензин. Для electric не заповнюй engine_volume: "
        "потужність із позначкою кВт/kw записуй в engine_power. Число з валютою — ціна; "
        "число після «пробіг»/mileage або перед км/km — пробіг; чотири цифри біля "
        "«рік/року»/year — рік. У короткому оголошенні окреме число 1900–2100 є роком, "
        "а окреме число понад 2100 без валюти — пробігом. Помилкові роздільники тисяч "
        "на кшталт 7,,200 означають 7200. Не вигадуй пропущені значення й не визначай колір."
    ),
    "rag.system": (
        "Відповідай українською, використовуючи лише надану базу знань компанії. "
        "Не вигадуй відсутні умови, гарантії, фінансування, наявність чи правила. "
        "Якщо контекст прямо не містить відповіді, поверни дослівно: {missing}"
    ),
    "rag.user": "КОНТЕКСТ:\n{context}\n\nЗАПИТАННЯ:\n{question}",
    "content.system": (
        "Створи український маркетинговий текст про автомобіль, використовуючи ЛИШЕ "
        "факти з запису БД. Не вигадуй комплектацію, гарантію, історію обслуговування, "
        "стан, ціну чи наявність. Пропускай відсутні факти. Фіксований блок про "
        "кредит/лізинг і телефони буде додано окремо. Стиль: {style}. {instruction}"
    ),
    "content.record": "ЗАПИС БД:\n{facts}",
    "content.instruction.short_description": "Створи короткий фактичний опис авто.",
    "content.instruction.website_description": "Створи структурований опис для сайту.",
    "content.instruction.telegram": (
        "Створи стислий допис для Telegram із нейтральним закликом написати менеджеру."
    ),
    "content.instruction.instagram": (
        "Створи підпис для Instagram; не вигадуй переваги або гарантію."
    ),
    "content.instruction.headline": "Створи один точний заголовок оголошення.",
    "content.instruction.advantages": "Перелічи лише переваги, підтверджені фактами.",
    "content.instruction.seo": "Створи фактичний SEO-опис без надлишку ключових слів.",
    "content.instruction.repost": "Створи альтернативну версію допису.",
    "content.instruction.faq_answer": "Відповідай, використовуючи лише факти про авто.",
}
