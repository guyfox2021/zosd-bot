from aiogram import Router
from aiogram.types import CallbackQuery

r = Router()

@r.callback_query()
async def debug_any_callback(call: CallbackQuery):
    print("🧩 CALLBACK DATA:", call.data)
    await call.answer()
