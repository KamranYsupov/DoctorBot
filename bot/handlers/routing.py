from aiogram import Router

from .start import router as start_router
from .fio import router as fio_router
from .protocol import router as protocol_router


def get_main_router():
    main_router = Router()

    main_router.include_router(start_router)
    main_router.include_router(fio_router)
    main_router.include_router(protocol_router)

    return main_router