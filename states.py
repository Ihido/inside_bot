from aiogram.fsm.state import StatesGroup, State

class ContentSubmission(StatesGroup):
    waiting_for_content_type = State()
    waiting_for_user_info = State()
    waiting_for_caption = State()
    waiting_for_media = State()
    waiting_for_confirmation = State()