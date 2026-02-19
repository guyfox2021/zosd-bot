from aiogram import Router
from aiogram.types import CallbackQuery

# отдельный router
r = Router()

@r.callback_query()
async def debug_any_callback(call: CallbackQuery):
    # печатает ВСЕ callback_data которые приходят
    print("🧩 CALLBACK DATA:", call.data)

    # чтобы у кнопки не крутился loading
    await call.answer()
