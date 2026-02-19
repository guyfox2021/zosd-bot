from aiogram import Router
from aiogram.types import CallbackQuery

r = Router()

@r.callback_query()
async def debug_any_callback(call: CallbackQuery):
    print("🧩 UNHANDLED CALLBACK DATA:", call.data)
    # Можно не отвечать, но лучше чтобы не крутило загрузку:
    await call.answer()
