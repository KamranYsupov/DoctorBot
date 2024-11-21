from aiogram import Router

from .start import router as start_router
from .fio import router as fio_router
from .protocol import router as protocol_router
from .edit_protocol import router as edit_protocol_router
from .menu import router as menu_router


def get_main_router():
    main_router = Router()

    main_router.include_router(start_router)
    main_router.include_router(fio_router)
    main_router.include_router(protocol_router)
    main_router.include_router(edit_protocol_router)
    main_router.include_router(menu_router)

    return main_router