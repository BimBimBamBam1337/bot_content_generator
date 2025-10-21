# from .admin import router as admin_router
from .comand import router as comand_router
from .callback import router as callback_router
from .message import router as message_router
from .voice import router as voice_router
from .script_generator import router as script_generator_router

routers = [
    comand_router,
    callback_router,
    message_router,
    voice_router,
    script_generator_router,
]
