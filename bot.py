import logging
import sys
import asyncio
from aiogram import Bot, Dispatcher, executor
from config import BOT_TOKEN
from handlers import start, media, audio, recognition
from services import TempFileCleaner

# Логирование
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

# Инициализация бота и диспетчера
bot = Bot(token=BOT_TOKEN, parse_mode="HTML")
dp = Dispatcher(bot)

# Регистрация хендлеров
start.register(dp)
media.register(dp)
audio.register(dp)
recognition.register(dp)

# Очистка временных файлов
cleaner = TempFileCleaner(max_age_minutes=30)


async def on_startup(dp):
    logger.info("🚀 Бот запущен!")
    asyncio.create_task(cleaner.start_auto_cleanup())


async def on_shutdown(dp):
    logger.info("🛑 Бот остановлен")
    cleaner.stop()


if __name__ == "__main__":
    executor.start_polling(
        dp,
        skip_updates=True,
        on_startup=on_startup,
        on_shutdown=on_shutdown
    )
