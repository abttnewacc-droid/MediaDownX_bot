from aiogram import types
from aiogram.dispatcher import Dispatcher
from utils.validators import URLValidator
from utils.helpers import extract_urls_from_text, safe_delete_file
from services import MediaDownloader
from keyboards.inline import InlineKeyboards
import asyncio

downloader = MediaDownloader()

# Хранилище активных загрузок
active_downloads = {}
# Хранилище результатов поиска
search_results = {}


async def handle_text_message(message: types.Message):
    """Обработка текстовых сообщений"""
    text = message.text

    # Извлечение URL из текста
    urls = extract_urls_from_text(text)

    if urls:
        # Обработка первого найденного URL
        url = urls[0]
        await process_url(message, url)
    else:
        # Проверка на поиск музыки (если нет URL)
        if len(text) > 3 and not text.startswith('/'):
            # Импорт обработчика поиска аудио
            from handlers.audio import search_audio
            await search_audio(message, text)


async def process_url(message: types.Message, url: str):
    """Обработка URL"""
    # Валидация URL
    if not URLValidator.is_valid_url(url):
        await message.answer(
            "❌ Неподдерживаемая ссылка.\n\n"
            "Поддерживаются: YouTube, Instagram, TikTok, Twitter/X, Pinterest и прямые ссылки на медиа."
        )
        return
    
    # Определение типа контента
    platform = URLValidator.detect_platform(url)
    
    # Отправка статуса
    status_msg = await message.answer("⏳ Анализирую ссылку...")
    
    try:
        # Проверка типа медиа
        if URLValidator.is_image_url(url):
            await process_image_url(message, url, status_msg)
        elif URLValidator.is_audio_url(url):
            await process_audio_url(message, url, status_msg)
        else:
            # Видео или неизвестный тип
            await process_video_url(message, url, status_msg)
    
    except Exception as e:
        await status_msg.edit_text(f"❌ Ошибка обработки: {str(e)}")


async def process_video_url(message: types.Message, url: str, status_msg: types.Message):
    """Обработка видео URL"""
    try:
        # Получение информации о видео
        await status_msg.edit_text("🔍 Получаю доступные качества...")
        
        qualities = await downloader.get_available_qualities(url)
        
        if not qualities:
            await status_msg.edit_text(
                "❌ Не удалось получить информацию о видео.\n"
                "Попробуйте другую ссылку или повторите позже."
            )
            return
        
        # Получение информации о видео
        info = await downloader.get_video_info(url)
        
        if info:
            title = info.get('title', 'Без названия')[:100]
            duration = info.get('duration', 0)
            
            info_text = f"📹 <b>{title}</b>\n"
            if duration:
                minutes = duration // 60
                seconds = duration % 60
                info_text += f"⏱ Длительность: {minutes}:{seconds:02d}\n"
            
            info_text += f"\n📊 Доступные качества:"
        else:
            info_text = "📊 Выберите качество:"
        
        # Отправка клавиатуры с качествами
        await status_msg.edit_text(
            info_text,
            reply_markup=InlineKeyboards.video_qualities(qualities, url)
        )
    
    except Exception as e:
        await status_msg.edit_text(f"❌ Ошибка: {str(e)}")


async def process_image_url(message: types.Message, url: str, status_msg: types.Message):
    """Обработка изображения"""
    try:
        await status_msg.edit_text("📥 Скачиваю изображение...")
        
        # Загрузка через yt-dlp (поддерживает Instagram, Pinterest и т.д.)
        image_file = await downloader.download_image(url)
        
        if not image_file or not image_file.exists():
            # Попытка прямой загрузки
            image_file = await downloader.download_direct_url(url)
        
        if image_file and image_file.exists():
            await status_msg.delete()
            
            # Отправка как документ (без сжатия)
            await message.answer_document(
                FSInputFile(image_file),
                caption="🖼 Изображение в оригинальном качестве"
            )
            
            # Удаление временного файла
            asyncio.create_task(safe_delete_file(image_file, delay=10))
        else:
            await status_msg.edit_text("❌ Не удалось скачать изображение")
    
    except Exception as e:
        await status_msg.edit_text(f"❌ Ошибка: {str(e)}")


async def process_audio_url(message: types.Message, url: str, status_msg: types.Message):
    """Обработка аудио URL"""
    try:
        await status_msg.edit_text("🎵 Скачиваю аудио...")
        
        # Загрузка
        audio_file = await downloader.download_video(url, audio_only=True)
        
        if audio_file and audio_file.exists():
            await status_msg.delete()
            
            # Отправка как аудио
            await message.answer_audio(
                FSInputFile(audio_file),
                caption="🎵 Аудио файл"
            )
            
            # Удаление временного файла
            asyncio.create_task(safe_delete_file(audio_file, delay=10))
        else:
            await status_msg.edit_text("❌ Не удалось скачать аудио")
    
    except Exception as e:
        await status_msg.edit_text(f"❌ Ошибка: {str(e)}")


async def callback_download_video(callback: types.CallbackQuery):
    """Callback скачивания видео в выбранном качестве"""
    try:
        # Парсинг данных: video:quality:url
        parts = callback.data.split(":", 2)
        quality = parts[1]
        url = parts[2]
        
        await callback.message.edit_text("⏳ Начинаю загрузку...")
        
        # Загрузка видео
        video_file = await downloader.download_video(
            url, 
            quality=quality,
            audio_only=False
        )
        
        if video_file and video_file.exists():
            await callback.message.edit_text("📤 Отправляю видео...")
            
            # Отправка как документ (без сжатия Telegram)
            await callback.message.answer_document(
                FSInputFile(video_file),
                caption=f"📹 Видео {quality if quality != 'best' else 'максимального качества'}"
            )
            
            await callback.message.delete()
            
            # Удаление временного файла
            asyncio.create_task(safe_delete_file(video_file, delay=30))
        else:
            await callback.message.edit_text(
                "❌ Не удалось скачать видео.\n"
                "Возможно, выбранное качество недоступно."
            )
        
        await callback.answer()
    
    except Exception as e:
        await callback.message.edit_text(f"❌ Ошибка: {str(e)}")
        await callback.answer()


async def callback_download_audio_only(callback: types.CallbackQuery):
    """Callback скачивания только аудио из видео"""
    try:
        # Парсинг данных: audio_only:url
        url = callback.data.split(":", 1)[1]
        
        await callback.message.edit_text("🎵 Извлекаю аудио...")
        
        # Загрузка аудио
        audio_file = await downloader.download_video(
            url, 
            audio_only=True
        )
        
        if audio_file and audio_file.exists():
            await callback.message.edit_text("📤 Отправляю аудио...")
            
            # Отправка как аудио
            await callback.message.answer_audio(
                FSInputFile(audio_file),
                caption="🎵 Аудио из видео (MP3 320kbps)"
            )
            
            await callback.message.delete()
            
            # Удаление временного файла
            asyncio.create_task(safe_delete_file(audio_file, delay=30))
        else:
            await callback.message.edit_text("❌ Не удалось извлечь аудио")
        
        await callback.answer()
    
    except Exception as e:
        await callback.message.edit_text(f"❌ Ошибка: {str(e)}")
        await callback.answer()


def register(dp: Dispatcher):
    dp.register_message_handler(handle_text_message, content_types=types.ContentTypes.TEXT)
    dp.register_callback_query_handler(callback_download_video, lambda c: c.data.startswith("video:"))
    dp.register_callback_query_handler(callback_download_audio_only, lambda c: c.data.startswith("audio_only:"))
