from __future__ import annotations

from datetime import date
from typing import Any

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.callbacks.factories import EventFlowCallback, MenuCallback
from app.core.dates import age_at, days_until
from app.core.formatting import format_countdown, format_date
from app.core.hebcal import format_hebrew_date, month_length, to_hebrew
from app.core.text import esc, split_name
from app.core.validators import (
    ValidationError,
    parse_gregorian,
    parse_hebrew_year_input,
    validate_name,
)
from app.core.gender_detector import detect_gender
from app.db.models import Event, User
from app.i18n.translator import t
from app.keyboards.events import (
    date_step_keyboard,
    hebrew_adar_choice_keyboard,
    hebrew_day_keyboard,
    hebrew_month_keyboard,
    hebrew_year_keyboard,
    name_step_keyboard,
    saved_keyboard,
)
from app.services.clock import user_today
from app.services.event_service import NewEventInput, create_minimal_event
from app.services.exceptions import LimitError
from app.services.reminder_service import describe_default_reminder
from app.states.forms import AddEvent
from app.utils.telegram import edit_or_ignore

router = Router(name="event_add")


@router.callback_query(MenuCallback.filter(F.action == "add"))
async def cb_menu_add(callback: CallbackQuery, user: User, state: FSMContext) -> None:
    await state.set_state(AddEvent.name)
    text = f"{t('add.name.title', user.language)}\n<i>{t('add.name.hint', user.language)}</i>"
    await edit_or_ignore(callback, text, name_step_keyboard(user.language))
    await callback.answer()


@router.message(AddEvent.name)
async def msg_add_name(message: Message, user: User, state: FSMContext) -> None:
    raw = message.text or ""
    try:
        cleaned = validate_name(raw)
    except ValidationError as exc:
        await message.answer(str(exc))
        return

    first_name, last_name = split_name(cleaned)
    await state.update_data(first_name=first_name, last_name=last_name)
    await state.set_state(AddEvent.date)
    
    gender = detect_gender(first_name)

    text = (
        f"{t('add.date.title', user.language, name=esc(first_name), gender=gender)}\n\n"
        f"{t('add.date.hint', user.language)}"
    )
    await message.answer(text, reply_markup=date_step_keyboard(user.language))


@router.message(AddEvent.date)
async def msg_add_date(message: Message, session: Any, user: User, state: FSMContext) -> None:
    raw = message.text or ""
    try:
        parsed = parse_gregorian(raw)
    except ValidationError as exc:
        await message.answer(str(exc))
        return

    event = await _finalize_event(
        session, user, state, month=parsed.month, day=parsed.day, year=parsed.year
    )
    if event is None:
        await message.answer(t("error.limit_reached", user.language, max=1000))
        return
    text = _render_saved_text(user, event)
    await message.answer(text, reply_markup=saved_keyboard(user.language, event.id))


@router.callback_query(AddEvent.date, EventFlowCallback.filter(F.action == "noyear"))
async def cb_add_no_year(callback: CallbackQuery, user: User, state: FSMContext) -> None:
    text = t("add.date.no_year_prompt", user.language)
    await edit_or_ignore(callback, text, date_step_keyboard(user.language))
    await callback.answer()


@router.callback_query(AddEvent.date, EventFlowCallback.filter(F.action == "heb"))
async def cb_add_hebrew_track(callback: CallbackQuery, user: User, state: FSMContext) -> None:
    await state.set_state(AddEvent.heb_month)
    await edit_or_ignore(
        callback, t("add.heb_month.title", user.language), hebrew_month_keyboard()
    )
    await callback.answer()


@router.callback_query(AddEvent.heb_month, EventFlowCallback.filter(F.action == "hm"))
async def cb_add_hebrew_month(
    callback: CallbackQuery, callback_data: EventFlowCallback, user: User, state: FSMContext
) -> None:
    month = int(callback_data.value or "0")

    data = await state.get_data()
    if month == 12 and not data.get("adar_choice_shown"):
        await state.update_data(adar_choice_shown=True)
        await edit_or_ignore(
            callback, t("add.heb_month.title", user.language), hebrew_adar_choice_keyboard()
        )
        await callback.answer()
        return

    await state.update_data(heb_month=month)
    await state.set_state(AddEvent.heb_day)

    current_hebrew_year, _, _ = to_hebrew(date.today())
    days_in_month = month_length(current_hebrew_year, month)
    await edit_or_ignore(
        callback, t("add.heb_day.title", user.language), hebrew_day_keyboard(days_in_month)
    )
    await callback.answer()


@router.callback_query(AddEvent.heb_day, EventFlowCallback.filter(F.action == "hd"))
async def cb_add_hebrew_day(
    callback: CallbackQuery, callback_data: EventFlowCallback, user: User, state: FSMContext
) -> None:
    day = int(callback_data.value or "0")
    await state.update_data(heb_day=day)
    await state.set_state(AddEvent.heb_year)

    heb_year_title = t("add.heb_year.title", user.language)
    heb_year_hint = t("add.heb_year.hint", user.language)
    text = f"{heb_year_title}\n<i>{heb_year_hint}</i>"
    await edit_or_ignore(callback, text, hebrew_year_keyboard(user.language))
    await callback.answer()


@router.callback_query(AddEvent.heb_year, EventFlowCallback.filter(F.action == "noyear"))
async def cb_add_hebrew_no_year(
    callback: CallbackQuery, session: Any, user: User, state: FSMContext
) -> None:
    data = await state.get_data()
    event = await _finalize_event(
        session,
        user,
        state,
        month=data["heb_month"],
        day=data["heb_day"],
        year=None,
        calendar_type="hebrew",
    )
    if event is None:
        await edit_or_ignore(callback, t("error.limit_reached", user.language, max=1000))
        await callback.answer()
        return
    text = _render_saved_text(user, event)
    await edit_or_ignore(callback, text, saved_keyboard(user.language, event.id))
    await callback.answer()


@router.message(AddEvent.heb_year)
async def msg_add_hebrew_year(
    message: Message, session: Any, user: User, state: FSMContext
) -> None:
    raw = message.text or ""
    try:
        year = parse_hebrew_year_input(raw)
    except ValidationError as exc:
        await message.answer(str(exc))
        return

    data = await state.get_data()
    event = await _finalize_event(
        session,
        user,
        state,
        month=data["heb_month"],
        day=data["heb_day"],
        year=year,
        calendar_type="hebrew",
    )
    if event is None:
        await message.answer(t("error.limit_reached", user.language, max=1000))
        return
    text = _render_saved_text(user, event)
    await message.answer(text, reply_markup=saved_keyboard(user.language, event.id))


async def _finalize_event(
    session: Any,
    user: User,
    state: FSMContext,
    *,
    month: int,
    day: int,
    year: int | None,
    calendar_type: str = "gregorian",
) -> Event | None:
    """Creates the event and clears FSM state. Returns None if the user's
    event limit was reached (caller renders the limit-reached message)."""
    data = await state.get_data()
    
    # Auto-detect gender
    gender = detect_gender(data["first_name"])
    
    try:
        event = await create_minimal_event(
            session,
            user,
            NewEventInput(
                first_name=data["first_name"],
                last_name=data.get("last_name"),
                month=month,
                day=day,
                year=year,
                calendar_type=calendar_type,
                gender=gender,
            ),
        )
    except LimitError:
        await state.clear()
        return None

    await state.clear()
    await state.update_data(event_id=event.id)
    return event


def _render_saved_text(user: User, event: Event) -> str:
    lang = user.language
    lines = [t("add.saved.title", lang, gender=event.gender), ""]

    name = esc(event.first_name)
    if event.last_name:
        name += f" {esc(event.last_name)}"
    lines.append(f"🎂 <b>{name}</b>")

    assert event.next_occurrence is not None  # always set by create_minimal_event

    if event.calendar_type == "hebrew":
        heb_str = format_hebrew_date(
            event.year or to_hebrew(event.next_occurrence)[0],
            event.month,
            event.day,
            with_year=event.year is not None,
        )
        lines.append(f"📅 {format_date(event.next_occurrence, user.date_format)}  ({heb_str})")
    else:
        lines.append(f"📅 {format_date(event.next_occurrence, user.date_format)}")

    countdown = format_countdown(days_until(event.next_occurrence, user_today(user)))
    lines.append(t("card.days_until", lang, countdown=countdown, gender=event.gender))

    age = age_at(event.calendar_type, event.year, event.month, event.day, event.next_occurrence)
    if age is not None:
        lines.append(t("card.age", lang, age=age, gender=event.gender))

    lines.append("")
    lines.append(t("add.saved.reminder", lang, reminder=describe_default_reminder(user), gender=event.gender))

    return "\n".join(lines)
