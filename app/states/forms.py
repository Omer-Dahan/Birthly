from __future__ import annotations

from aiogram.fsm.state import State, StatesGroup


class Onboarding(StatesGroup):
    language = State()
    timezone = State()
    timezone_custom = State()
    notify_time = State()
    notify_time_custom = State()


class AddEvent(StatesGroup):
    name = State()
    date = State()
    heb_month = State()
    heb_day = State()
    heb_year = State()


class EditEvent(StatesGroup):
    choosing_field = State()
    entering_value = State()
    heb_month = State()
    heb_day = State()
    heb_year = State()


class Search(StatesGroup):
    query = State()


class SettingsFlow(StatesGroup):
    custom_time = State()
    custom_timezone = State()
    wipe_confirm = State()


class TemplateFlow(StatesGroup):
    body = State()
    tone = State()


class ImportFlow(StatesGroup):
    waiting_file = State()
    confirm = State()


class AdminFlow(StatesGroup):
    broadcast_text = State()
    broadcast_confirm = State()
