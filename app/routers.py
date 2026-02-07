from aiogram import Router

from app.handlers.user_start import r as user_start_router
from app.handlers.user_tickets import r as user_ticket_router
from app.handlers.cheatsheet import r as cheat_router
from app.handlers.admin_panel import r as admin_panel_router
from app.handlers.admin_reply import r as admin_reply_router
from app.handlers.admin_broadcast import r as admin_broadcast_router
from app.handlers.admin_cheatsheet import r as admin_cheat_router

router = Router()
router.include_router(user_start_router)
router.include_router(user_ticket_router)
router.include_router(cheat_router)

router.include_router(admin_panel_router)
router.include_router(admin_reply_router)
router.include_router(admin_broadcast_router)
router.include_router(admin_cheat_router)
