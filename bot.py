import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher
from aiogram.types import ParseMode
from config import BOT_TOKEN
from handlers import (
    start_register,
    media_register,
    audio_register,
    recognition_register,
)
from services import TempFileCleaner

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


async def main():
    """Главная функция запуска бота"""
    
    # Инициализация бота
    bot = Bot(token=BOT_TOKEN, parse_mode=ParseMode.HTML)
    
    dp = Dispatcher(bot)
    
    # Регистрация обработчиков
    start_register(dp)
    media_register(dp)
    audio_register(dp)
    recognition_register(dp)
    
    # Запуск автоочистки временных файлов
    cleaner = TempFileCleaner(max_age_minutes=30)
    asyncio.create_task(cleaner.start_auto_cleanup())
    
    logger.info("🚀 Бот запущен!")
    
    try:
        # Удаление вебхука (для polling)
        await bot.delete_webhook(drop_pending_updates=True)
        
        # Запуск polling
        await dp.start_polling(bot, skip_updates=False)
    
    finally:
        # Остановка автоочистки
        cleaner.stop()
        await bot.session.close()
        logger.info("🛑 Бот остановлен")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("⚠️ Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
