import logging
import sys
import asyncio

from aiogram import Bot, Dispatcher
from aiogram.utils import executor
from aiogram.types import ParseMode

from config import BOT_TOKEN
from handlers import (
    start_register,
    media_register,
    audio_register,
    recognition_register,
)
from services import TempFileCleaner

# ─── ЛОГИ ─────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

# ─── БОТ И DP ─────────────────────────────────────────────────────────
bot = Bot(token=BOT_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher(bot)

# ─── РЕГИСТРАЦИЯ ХЕНДЛЕРОВ ────────────────────────────────────────────
start_register(dp)
media_register(dp)
audio_register(dp)
recognition_register(dp)

# ─── CLEANER ──────────────────────────────────────────────────────────
cleaner = TempFileCleaner(max_age_minutes=30)

# ─── STARTUP / SHUTDOWN ───────────────────────────────────────────────
async def on_startup(dispatcher: Dispatcher):
    # гарантированно убираем вебхук и старые апдейты
    await bot.delete_webhook(drop_pending_updates=True)
    asyncio.create_task(cleaner.start_auto_cleanup())
    logger.info("🚀 Бот запущен!")

async def on_shutdown(dispatcher: Dispatcher):
    cleaner.stop()
    await bot.session.close()
    logger.info("🛑 Бот остановлен")

# ─── ЗАПУСК ───────────────────────────────────────────────────────────
if __name__ == "__main__":
    executor.start_polling(
        dp,
        on_startup=on_startup,
        on_shutdown=on_shutdown,
        skip_updates=True,
    )
