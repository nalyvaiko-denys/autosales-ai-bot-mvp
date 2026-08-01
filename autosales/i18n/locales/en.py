"""English language resources."""

LANGUAGE = "en"

BUTTONS = {
    "language.uk": "Українська",
    "language.en": "English",
    "contact.share": "📱 Share phone number",
    "menu.search": "🔎 Find a car",
    "menu.catalog": "🚘 Catalog",
    "menu.favorites": "⭐ Favorites",
    "menu.manager": "💬 Message a manager",
    "menu.ai_search": "✨ AI car search",
    "menu.ai_assistant": "🤖 AI assistant",
    "menu.my_leads": "📋 My requests",
    "menu.question": "❓ Ask a question",
    "menu.manager_legacy": "👤 Contact a manager",
    "car.gallery": "🖼 Open gallery",
    "car.favorite_add": "⭐ Add to favorites",
    "car.favorite_remove": "❌ Remove from favorites",
    "car.manager": "💬 Ask a manager",
    "navigation.previous": "← Previous",
    "navigation.next": "Next →",
    "admin.menu.stats": "📊 Statistics",
    "admin.menu.inventory": "🚗 Vehicle inventory",
    "admin.menu.create_car": "➕ Add a vehicle",
    "admin.menu.leads": "📥 Customer requests",
    "admin.menu.appointments": "📅 Viewing appointments",
    "admin.menu.content": "📝 Content drafts",
    "admin.menu.ai_help": "🧠 How LangGraph works",
    "admin.menu.exit": "↩️ Exit admin mode",
    "admin.publish_done": "✅ Finish publishing",
    "admin.cancel": "❌ Cancel",
    "admin.photo_done": "✅ Photos uploaded",
    "admin.car.edit": "✏️ Edit",
    "admin.car.photos": "📷 Photos",
    "admin.car.gallery": "🖼 Gallery",
    "admin.car.archive": "🗄 Archive",
    "admin.car.delete": "🗑 Delete",
    "admin.inventory.all_locations": "All locations",
    "admin.car.add_photo": "➕ Add photos",
    "admin.car.cover": "Cover #{position}",
    "admin.field.name": "Vehicle name",
    "admin.field.year": "Year",
    "admin.field.price": "Price",
    "admin.field.fuel": "Fuel",
    "admin.field.transmission": "Transmission",
    "admin.field.engine": "Engine volume",
    "admin.field.status": "Status",
    "admin.field.location": "Address",
    "admin.confirm.archive": "Yes, archive",
    "admin.confirm.delete": "Yes, delete",
    "admin.action.contact": "📞 Contact",
    "admin.action.edit": "✏️ Edit",
    "admin.action.delete_lead": "🗑 Delete request",
    "admin.action.delete_appointment": "🗑 Delete appointment",
    "admin.action.back": "← Back",
    "admin.action.approve": "✅ Approve",
    "admin.action.reject": "❌ Reject",
}

TEXTS = {
    "language.choose": "Оберіть мову / Choose language",
    "welcome": "Welcome, {name}!",
    "registration.ask_name": "What should we call you?",
    "registration.ask_contact": "Share your phone number using the Telegram button.",
    "registration.own_contact": "Please share your own contact using the button below.",
    "registration.completed": "Registration completed ✅",
    "language.changed": "Language changed ✅",
    "start.required": "Please run /start first",
    "start.registration_required": "Please complete registration with /start first.",
    "car.address": "Address",
    "car.liter": "L",
    "car.kilometer": "km",
    "car.finance": "Credit or leasing is available",
    "catalog.error": "An error occurred while loading the catalog. Please try again.",
    "catalog.empty": "There are currently no available cars in the catalog.",
    "catalog.heading": "🚘 <b>Catalog · page {page}/{pages}</b>",
    "catalog.count": "Cars: {total}. On this page: {count}.",
    "catalog.render_error": "An error occurred while displaying the cars. Please try again.",
    "catalog.navigation": "Go to another page:",
    "catalog.busy": "The catalog is already loading. Please wait a few seconds.",
    "catalog.page_busy": "This page is already loading",
    "catalog.loading": "Loading page…",
    "search.prompt": (
        "Enter one or more criteria in plain language. For example: "
        "“Toyota”, “under $15,000”, “from 2018”, or a complete car description."
    ),
    "search.ai_prompt": (
        "Describe the car in plain language: make, budget, year, mileage, fuel, or transmission."
    ),
    "assistant.prompt": (
        "Write a plain-language description with no special format. For example: "
        "“Mazda 3, mileage under 100,000 km, price under $9,890, 1.4 petrol, "
        "automatic, from 2011”."
    ),
    "search.refinement": "User clarification: {text}",
    "search.processing": "Processing your request…",
    "search.failed": "The request could not be processed. Please clarify it and try again.",
    "search.clarify_numbers": "Please clarify the numeric parameters.",
    "search.not_found": "No cars were found for your request.",
    "search.found": "Found {count} cars. Here are the results:",
    "search.why": "Why it matches:",
    "search.match": "Match: {score}",
    "search.error": "An error occurred during the search. Please try again later.",
    "search.error_code": "Error code: <code>{error_id}</code>",
    "search.ambiguous": (
        "Please clarify whether {values} means price, year, or mileage. For example: "
        "“price 5000 EUR, from 1998, mileage under 150,000 km”. "
        "Commas, periods, and hyphens are optional."
    ),
    "search.no_candidates": (
        "No available cars match the required criteria. Tell me which parameter "
        "can be changed; the budget will not be exceeded."
    ),
    "search.objective_only": (
        "Provide at least one objective criterion: make, model, price, year, mileage, fuel, "
        "transmission, or body type. Subjective labels such as reliable or economical are "
        "not used for search."
    ),
    "favorite.added": "Added to favorites ⭐",
    "favorite.removed": "Removed from favorites",
    "favorite.empty": "Your favorites list is empty.",
    "gallery.unavailable": "This car is no longer available",
    "gallery.empty": "There are no photos for this car yet",
    "lead.request_message": "The customer would like to be contacted about this car",
    "lead.transferred": "Your request was sent to a manager",
    "lead.thanks": "Thank you. A manager received your request and will contact you.",
    "lead.error": "Your request could not be sent to a manager. Please try again.",
    "lead.error_code": "Error code: <code>{error_id}</code>",
    "lead.manager_claimed": "A manager has received your request and will contact you.",
    "appointment.ask_date": (
        "Enter your preferred date and time as <code>2026-08-15 14:30</code>. "
        "A manager will confirm it manually."
    ),
    "appointment.invalid_date": "The date could not be recognized. Example: 2026-08-15 14:30",
    "appointment.created": (
        "Viewing request #{appointment_id} was created. Please wait for manager confirmation."
    ),
    "appointment.manager_claimed": (
        "A manager has received your viewing request and will contact you."
    ),
    "appointment.reminder": (
        "Reminder: the viewing for car #{car_id} is scheduled for {appointment_at}."
    ),
    "appointment.status_update": ("Viewing #{appointment_id}: {status}, {appointment_at}."),
    "leads.empty": "You do not have any requests yet.",
    "leads.item": "#{lead_id} · {status} · car {car}",
    "leads.no_car": "not selected",
    "lead.status_update": "Your request #{lead_id} status: {status}.",
    "question.prompt": "Ask a question about buying, reservations, or our locations.",
    "manager.prompt": "Briefly describe your question and a manager will receive it.",
    "manager.thanks": "Thank you. A manager received your message and will contact you.",
    "explanation.price": "price {price} {currency} is within budget",
    "explanation.year": "year {year}",
    "explanation.mileage": "mileage {mileage} km",
    "explanation.engine": "{volume} L engine",
    "explanation.transmission": "{transmission} transmission",
    "explanation.fuel": "{fuel}",
    "explanation.body": "{body} body type",
    "rag.missing": "This information is not specified. I will ask a manager to clarify it.",
    "content.manager_details": "Ask a manager for details and current availability.",
    "content.phones": "Phone numbers: {phones}.",
    "content.price": "Price: {price} {currency}.",
    "content.fuel": "Fuel: {fuel}.",
    "content.transmission": "Transmission: {transmission}.",
    "content.drive": "Drive: {drive}.",
    "content.mileage": "Mileage: {mileage} km.",
    "fuel.petrol": "petrol",
    "fuel.diesel": "diesel",
    "fuel.gas": "LPG",
    "fuel.hybrid": "hybrid",
    "fuel.electric": "electric",
    "transmission.automatic": "automatic",
    "transmission.manual": "manual",
    "drive.awd": "all-wheel drive",
    "drive.fwd": "front-wheel drive",
    "drive.rwd": "rear-wheel drive",
    "drive.not_specified": "not specified",
    "body.crossover": "crossover",
    "body.suv": "SUV",
    "body.sedan": "sedan",
    "body.hatchback": "hatchback",
    "body.wagon": "wagon",
    "body.minivan": "minivan",
    "body.coupe": "coupe",
    "body.liftback": "liftback",
    "body.not_specified": "not specified",
    "car_status.available": "available",
    "car_status.reserved": "reserved",
    "car_status.sold": "sold",
    "car_status.archived": "archived",
    "lead_status.new": "new",
    "lead_status.in_progress": "in progress",
    "lead_status.contacted": "manager is contacting you",
    "lead_status.appointment_scheduled": "viewing scheduled",
    "lead_status.test_drive_completed": "test drive completed",
    "lead_status.reserved": "reserved",
    "lead_status.won": "successfully completed",
    "lead_status.lost": "closed",
    "lead_status.spam": "not relevant",
    "content_status.draft": "draft",
    "content_status.approved": "approved",
    "content_status.rejected": "rejected",
    "content_status.published": "published",
    "appointment_status.pending": "waiting for a manager",
    "appointment_status.confirmed": "confirmed",
    "appointment_status.completed": "completed",
    "appointment_status.cancelled": "cancelled",
    "currency.USD": "USD",
    "currency.EUR": "EUR",
    "currency.UAH": "UAH",
    "command.start": "Main menu",
    "command.ai": "LangGraph AI assistant",
    "command.id": "Show my Telegram ID",
    "command.admin": "Telegram admin panel",
    "command.language": "Change language",
    "admin.state.waiting": "waiting for a manager",
    "admin.state.claimed": "a manager is already contacting the customer",
    "admin.no_car": "no vehicle",
    "admin.not_specified": "not specified",
    "admin.unknown_user": "unknown",
    "admin.lead.card": (
        "📥 <b>Request #{lead_id}</b>\n"
        "Status: {state}\n"
        "Customer: {customer}\n"
        "Phone: <code>{phone}</code>\n"
        "Vehicle: {car}\n"
        "Message: {message}"
    ),
    "admin.appointment.card": (
        "📅 <b>Viewing request #{appointment_id}</b>\n"
        "Status: {state}\n"
        "Preferred time: {appointment_at}\n"
        "Customer: {customer}\n"
        "Phone: <code>{phone}</code>\n"
        "Vehicle: {car}"
    ),
    "admin.access_denied": (
        "⛔️ You do not have access to the Telegram admin panel.\n"
        "Your Telegram ID: <code>{user_id}</code>\n"
        "Add it to <code>TELEGRAM_ADMIN_IDS</code> in .env and restart the bot."
    ),
    "admin.access_denied_short": "Access denied",
    "admin.access_denied_inventory": ("⛔️ Access denied. Add your ID to TELEGRAM_ADMIN_IDS."),
    "admin.telegram_id": "Your Telegram ID: <code>{user_id}</code>",
    "admin.enter": "🔐 <b>Telegram admin panel</b>\nChoose a section:",
    "admin.closed": "Admin mode closed.",
    "admin.stats": (
        "📊 <b>Statistics</b>\n"
        "Customers: {customers}\n"
        "Requests: {leads}\n"
        "Appointments: {appointments}\n"
        "Available vehicles: {available_cars}\n"
        "Sold: {sold_cars}\n"
        "Request → appointment conversion: {lead_conversion}\n"
        "Appointment → sale conversion: {sale_conversion}"
    ),
    "admin.leads.empty": "There are no customer requests yet.",
    "admin.leads.heading": "📥 <b>Latest requests and viewing appointments</b>",
    "admin.content.empty": "There are no drafts awaiting approval.",
    "admin.content.card": (
        "📝 <b>Content #{content_id}</b> · {content_type}\nVehicle: {car}\n\n{content}"
    ),
    "admin.ai_help": (
        "🧠 <b>LangGraph in this bot</b>\n\n"
        "The <b>🤖 AI assistant</b> button or /ai command runs this graph:\n"
        "<code>classify → search | knowledge</code>\n\n"
        "• vehicle search: “Which Audi cars are currently available?”;\n"
        "• knowledge base: “Which documents are required for a test drive?”.\n\n"
        "LangGraph manages routing and state. A separate full LangChain layer is not "
        "needed: the graph already uses langchain-core, while SQL filters and RAG remain "
        "controlled."
    ),
    "admin.inventory.module_missing": (
        "Restart the bot: the vehicle management module is not connected."
    ),
    "admin.confirm_delete": "Confirm deletion",
    "admin.lead.deleted_message": "🗑 Request #{lead_id} deleted.",
    "admin.lead.deleted": "Request deleted",
    "admin.lead.already_deleted": "The request has already been deleted",
    "admin.lead.already_claimed": "Another manager has already claimed this request",
    "admin.lead.claimed": "Request claimed. You can now call the customer.",
    "admin.appointment.deleted_message": "🗑 Appointment #{appointment_id} deleted.",
    "admin.appointment.deleted": "Appointment deleted",
    "admin.appointment.already_deleted": "The appointment has already been deleted",
    "admin.appointment.already_claimed": ("Another manager has already claimed this appointment"),
    "admin.appointment.claimed": "Appointment claimed. You can now call the customer.",
    "admin.unknown_action": "Unknown action",
    "admin.operation_failed": "The action failed. Refresh the section and try again.",
    "admin.invalid_status": "Invalid status",
    "admin.content.updated": "Content #{content_id}: {status}",
    "admin.inventory.empty": "The vehicle inventory is empty.",
    "admin.inventory.heading": "Latest vehicles across all statuses:",
    "admin.inventory.filter_choose": "Choose which location's vehicles to display:",
    "admin.inventory.loading_location": "Loading vehicles for this location…",
    "admin.inventory.empty_for_location": "There are no vehicles at “{location}”.",
    "admin.inventory.heading_filtered": ("🚗 <b>{location}</b>\nVehicles found: {count}"),
    "admin.inventory.cancelled": "Action cancelled.",
    "admin.inventory.unrecognized": "not recognized",
    "admin.inventory.recognized": (
        "<b>Recognized from the description:</b>\n"
        "Vehicle: {name}\n"
        "Year: {year}\n"
        "Transmission: {transmission}\n"
        "Engine: {engine} L\n"
        "Fuel: {fuel}\n"
        "Price: {price} {currency}\n"
        "Mileage: {mileage} km"
    ),
    "admin.inventory.card": (
        "<b>#{car_id} · {brand} {model} · {year}</b>\n"
        "💵 {price} {currency}\n"
        "⚙️ {details}\n"
        "📍 Address: {location}\n"
        "Status: <b>{status}</b>{mileage}"
    ),
    "admin.inventory.card_mileage": "\nMileage: {mileage} km",
    "admin.inventory.prompt.name": ("Enter the vehicle make and model, for example Mazda 3:"),
    "admin.inventory.prompt.year": "Enter the production year, for example 2021:",
    "admin.inventory.prompt.price": "Enter the price, for example $18,500:",
    "admin.inventory.prompt.fuel_type": (
        "Enter the fuel type: petrol, diesel, LPG, hybrid, or electric:"
    ),
    "admin.inventory.prompt.transmission": ("Enter the transmission: automatic or manual:"),
    "admin.inventory.prompt.engine_volume": ("Enter the engine volume, for example 1.4 or 2.0:"),
    "admin.inventory.location_missing": (
        "There are no active locations. Add an address in the web CRM."
    ),
    "admin.inventory.location_choose": "Choose a location:",
    "admin.inventory.create_failed": "The draft could not be created: {error}",
    "admin.inventory.draft_created": (
        "Draft #{car_id} created. Send up to {max_photos} photos as an album or "
        "separately. The first photo will become the cover."
    ),
    "admin.inventory.create_intro": (
        "Send one plain-language vehicle description. I will fill in the post and ask "
        "only for information that is actually missing.\n\n"
        "Example: <code>Mazda 3, mileage 10000 km, price $9890, 1.4 petrol, "
        "automatic, year 2011, Mekhanizatoriv</code>\n\n"
        "Address 1 — Kyivske Highway, 41A; address 2 — Mekhanizatoriv, 1A."
    ),
    "admin.inventory.recognizing": "Recognizing vehicle data…",
    "admin.inventory.error.name": "Enter both make and model. Example: Mazda 3.",
    "admin.inventory.error.year": "The year must be a number from 1900 to 2100.",
    "admin.inventory.error.transmission": "Enter “automatic” or “manual”.",
    "admin.inventory.error.engine": "Enter a numeric engine volume, such as 1.4 or 2.0.",
    "admin.inventory.error.fuel": ("Enter petrol, diesel, LPG, hybrid, or electric."),
    "admin.inventory.error.price": ("Enter a positive price, for example $9,890 or 9,200 EUR."),
    "admin.inventory.photo_added_count": "Photo added. Total: {count}.",
    "admin.inventory.photo_required": "Add at least one photo.",
    "admin.inventory.saved": "Vehicle #{car_id} saved, photos: {photo_count} ✅",
    "admin.inventory.edit_choose": "What should be changed for vehicle #{car_id}?",
    "admin.inventory.status_choose": "Choose a new status:",
    "admin.inventory.location_new_choose": "Choose a new location:",
    "admin.inventory.invalid_value": "Invalid value: {error}",
    "admin.inventory.updated": "Vehicle #{car_id} updated ✅",
    "admin.inventory.status_updated": "New status: {status}",
    "admin.inventory.location_updated": "Location for vehicle #{car_id} changed",
    "admin.inventory.location_updated_to": (
        "Vehicle #{car_id} moved to “{location}” ✅ The inventory has been updated."
    ),
    "admin.inventory.photos": (
        "Vehicle #{car_id} photos: {count}. Tap a number to make it the cover."
    ),
    "admin.inventory.photos_add": (
        "Send additional photos separately or as an album, then tap the button below."
    ),
    "admin.inventory.photo_added": "Photo added.",
    "admin.inventory.photos_saved": "Photos saved ✅",
    "admin.inventory.cover_changed": "Cover changed ⭐",
    "admin.inventory.photos_empty": "This vehicle does not have any photos yet",
    "admin.inventory.cover_caption": "⭐ Cover",
    "admin.inventory.archive_confirm": (
        "The vehicle will disappear from the customer catalog but remain in the database "
        "and can be restored by changing its status. Continue?"
    ),
    "admin.inventory.archived": "Vehicle #{car_id} moved to the archive",
    "admin.inventory.archive_cancelled": "Archiving cancelled",
    "admin.inventory.delete_confirm": (
        "⚠️ This permanently deletes the listing, its photos, and listing-specific records "
        "from the database. This action cannot be undone."
    ),
    "admin.inventory.deleted": "Vehicle #{car_id} permanently deleted",
    "admin.inventory.already_deleted": "This vehicle has already been deleted",
    "admin.inventory.delete_cancelled": "Deletion cancelled",
}

PROMPTS = {
    "criteria.system": (
        "Extract car-search criteria from Ukrainian or English text. Normalize body types "
        "to crossover/suv/sedan/hatchback/wagon/minivan/coupe, fuel to "
        "petrol/diesel/gas/hybrid/electric, and transmission to automatic/manual. "
        "Extract only explicitly stated brand, model, currency, and engine volume. "
        "Punctuation and word order are optional. Never guess whether an unlabeled number "
        "is a price, year, or mileage. Numeric upper limits are hard. Do not extract or "
        "infer color: visual appearance is not structured inventory data. Do not turn "
        "subjective phrases such as reliable, economical, first car, family car, or "
        "comfortable into search criteria. Do not infer facts the user did not state."
    ),
    "car_draft.system": (
        "Convert a Ukrainian or English free-text vehicle listing into structured fields: "
        "brand, model, production year, transmission, engine volume, fuel, price, currency, "
        "mileage, body type, and drive type. Normalize transmission to automatic/manual, "
        "fuel to petrol/diesel/gas/hybrid/electric, and drive to fwd/rwd/awd. A number with "
        "a currency is price; a number after mileage/пробіг or before km/км is mileage; a "
        "four-digit number near year/рік/року is the year. In a short listing, a standalone "
        "number from 1900 to 2100 is the year, and a standalone number over 2100 without a "
        "currency is mileage. Treat malformed thousand separators such as 7,,200 as 7200. "
        "Never invent missing values or infer color."
    ),
    "rag.system": (
        "Answer in English using only the supplied company knowledge. Do not infer missing "
        "terms, guarantees, financing, availability, or policies. If the context does not "
        "explicitly answer the question, reply exactly: {missing}"
    ),
    "rag.user": "CONTEXT:\n{context}\n\nQUESTION:\n{question}",
    "content.system": (
        "Create English-language vehicle marketing copy using ONLY facts in the supplied "
        "database record. Never invent options, warranty, service history, condition, price, "
        "or availability. Omit absent facts. The fixed credit/leasing and phone footer is "
        "appended separately. Style: {style}. {instruction}"
    ),
    "content.record": "DATABASE RECORD:\n{facts}",
    "content.instruction.short_description": "Create a short factual car description.",
    "content.instruction.website_description": ("Create a structured factual website description."),
    "content.instruction.telegram": (
        "Create a concise Telegram post with a neutral call to contact a manager."
    ),
    "content.instruction.instagram": (
        "Create an Instagram caption; do not invent benefits or warranty."
    ),
    "content.instruction.headline": "Create one accurate listing headline.",
    "content.instruction.advantages": (
        "List only advantages directly supported by the supplied facts."
    ),
    "content.instruction.seo": "Create a factual SEO description without keyword stuffing.",
    "content.instruction.repost": "Create an alternate factual listing post.",
    "content.instruction.faq_answer": "Answer using only the supplied car facts.",
}
