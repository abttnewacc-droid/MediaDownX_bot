from aiogram import types
from aiogram.dispatcher import Dispatcher
from aiogram.types.input_file import InputFile
from utils.validators import URLValidator
from utils.helpers import extract_urls_from_text, safe_delete_file, format_duration
from services import MediaDownloader
from keyboards.inline import InlineKeyboards
import asyncio
import logging

logger = logging.getLogger(__name__)

downloader = MediaDownloader()

# Хранилище активных загрузок
active_downloads = {}
# Хранилище результатов поиска
search_results = {}


async def handle_text_message(message: types.Message):
    text = message.text.strip()

    urls = extract_urls_from_text(text)
    if urls:
        await process_url(message, urls[0])
        return

    if len(text) > 3 and not text.startswith('/'):
        from handlers.audio import search_audio
        await search_audio(message, text)


async def process_url(message: types.Message, url: str):
    if not URLValidator.is_valid_url(url):
        await message.answer(
            "❌ Неподдерживаемая ссылка.\n\n"
            "Поддерживаются: YouTube, Instagram, TikTok, Twitter/X, Pinterest и прямые ссылки."
        )
        return

    platform = URLValidator.detect_platform(url)
    status_msg = await message.answer("⏳ Анализирую ссылку...")

    try:
        # Прямые файлы
        if platform == "direct":
            if URLValidator.is_image_url(url):
                await process_image_url(message, url, status_msg)
            elif URLValidator.is_audio_url(url):
                await process_audio_url(message, url, status_msg)
            else:
                await process_video_url(message, url, status_msg)
            return

        # Соцсети — ВСЕГДА через yt-dlp как видео
        await process_video_url(message, url, status_msg)

    except Exception as e:
        logger.exception(e)
        await status_msg.edit_text("❌ Ошибка обработки ссылки.")


async def process_video_url(message: types.Message, url: str, status_msg: types.Message):
    await status_msg.edit_text("🔍 Анализирую видео…")

    info = await downloader.get_video_info(url)
    if not info:
        await status_msg.edit_text("❌ Не удалось получить информацию о видео.")
        return

    qualities = await downloader.get_available_qualities(url)
    if not qualities:
        await status_msg.edit_text("❌ Не удалось получить доступные качества.")
        return

    title = info.get("title", "Без названия")[:100]
    duration = info.get("duration")

    text = f"📹 <b>{title}</b>\n"
    if duration:
        text += f"⏱ {format_duration(int(duration))}\n"
    text += "\n📊 Выбери качество:"

    await status_msg.edit_text(
        text,
        reply_markup=InlineKeyboards.video_qualities(qualities, url)
    )


async def process_image_url(message: types.Message, url: str, status_msg: types.Message):
    await status_msg.edit_text("📥 Скачиваю изображение…")

    image_file = await downloader.download_image(url)
    if not image_file or not image_file.exists():
        image_file = await downloader.download_direct_url(url)

    if not image_file or not image_file.exists():
        await status_msg.edit_text("❌ Не удалось скачать изображение.")
        return

    await status_msg.delete()
    await message.answer_document(
        InputFile(image_file),
        caption="🖼 Оригинальное изображение"
    )
    asyncio.create_task(safe_delete_file(image_file, delay=15))


async def process_audio_url(message: types.Message, url: str, status_msg: types.Message):
    await status_msg.edit_text("🎵 Скачиваю аудио…")

    audio_file = await downloader.download_video(url, audio_only=True)
    if not audio_file or not audio_file.exists():
        await status_msg.edit_text("❌ Не удалось скачать аудио.")
        return

    await status_msg.delete()
    await message.answer_audio(
        InputFile(audio_file),
        caption="🎵 Аудио файл"
    )
    asyncio.create_task(safe_delete_file(audio_file, delay=15))


async def callback_download_video(callback: types.CallbackQuery):
    data = callback.data
    _, quality, url = data.split(":", 2)

    await callback.message.edit_text("⏳ Загружаю видео…")

    video_file = await downloader.download_video(url, quality=quality)
    if not video_file or not video_file.exists():
        await callback.message.edit_text("❌ Не удалось скачать видео.")
        await callback.answer()
        return

    await callback.message.answer_document(
        InputFile(video_file),
        caption=f"📹 Видео {quality if quality != 'best' else 'максимального качества'}"
    )
    await callback.message.delete()
    asyncio.create_task(safe_delete_file(video_file, delay=30))
    await callback.answer()


async def callback_download_audio_only(callback: types.CallbackQuery):
    url = callback.data[len("audio_only:"):]
    await callback.message.edit_text("🎵 Извлекаю аудио…")

    audio_file = await downloader.download_video(url, audio_only=True)
    if not audio_file or not audio_file.exists():
        await callback.message.edit_text("❌ Не удалось извлечь аудио.")
        await callback.answer()
        return

    await callback.message.answer_audio(
        InputFile(audio_file),
        caption="🎵 Аудио из видео (320 kbps)"
    )
    await callback.message.delete()
    asyncio.create_task(safe_delete_file(audio_file, delay=30))
    await callback.answer()


def register(dp: Dispatcher):
    dp.register_message_handler(handle_text_message, content_types=["text"])
    dp.register_callback_query_handler(callback_download_video, lambda c: c.data.startswith("video:"))
    dp.register_callback_query_handler(callback_download_audio_only, lambda c: c.data.startswith("audio_only:"))
