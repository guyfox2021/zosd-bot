from aiogram.fsm.state import State, StatesGroup


class UserTicket(StatesGroup):
    waiting_text = State()


class AdminReply(StatesGroup):
    waiting_answer = State()


class AdminBroadcast(StatesGroup):
    waiting_text = State()


class AdminCheat(StatesGroup):
    creating_section = State()
    renaming_section = State()
    creating_item_title = State()
    creating_item_content = State()
    editing_item_title = State()
    editing_item_content = State()
