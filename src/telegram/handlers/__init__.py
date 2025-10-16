# from .admin import router as admin_router
from .comand import router as comand_router
from .callback import router as callback_router
from .message import router as message_router

routers = [comand_router, callback_router, message_router]
