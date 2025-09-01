import asyncio
import logging

from aiogram.fsm.storage.memory import MemoryStorage

from config.settings import settings

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties

from src.handlers import \
    main_handler, \
    photo_handler, \
    link_handler,  \
    size_handler,  \
    color_handler,  \
    price_handler,  \
    qty_handler,  \
    submit_handler

async def main():
    logging.basicConfig(level=logging.INFO)

    bot = Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode='HTML')
    )

    dp = Dispatcher(storage=MemoryStorage())
    dp.include_routers(
        main_handler.router,
        photo_handler.router,
        link_handler.router,
        size_handler.router,
        color_handler.router,
        price_handler.router,
        qty_handler.router,
        submit_handler.router
    )

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
