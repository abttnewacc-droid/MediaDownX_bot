from aiogram import types
from aiogram.dispatcher import Dispatcher
from keyboards.inline import InlineKeyboards
from services import MusicRecognizer
from utils.helpers import safe_delete_file
from config import TEMP_DIR
import asyncio
from pathlib import Path

recognizer = MusicRecognizer()


async def recognize_audio(message: types.Message):
    try:
        status_msg = await message.answer("🎵 Распознаю трек...")

        file_path = TEMP_DIR / f"audio_{message.from_user.id}_{message.audio.file_id}.mp3"
        file = await message.bot.download(message.audio, destination=file_path)

        if not file or not file.exists():
            await status_msg.edit_text("❌ Не удалось скачать аудио")
            return

        track_info = await recognizer.recognize_from_file(file)
        asyncio.create_task(safe_delete_file(file, delay=5))

        if track_info:
            await status_msg.edit_text(
                recognizer.format_track_info(track_info),
                reply_markup=InlineKeyboards.recognized_track(track_info)
            )
        else:
            await status_msg.edit_text(
                "❌ Не удалось распознать трек.\n"
                "Попробуйте загрузить более качественный фрагмент."
            )

    except Exception as e:
        await message.answer(f"❌ Ошибка распознавания: {e}")


async def recognize_voice(message: types.Message):
    try:
        status_msg = await message.answer("🎵 Распознаю музыку из голосового...")

        file_path = TEMP_DIR / f"voice_{message.from_user.id}_{message.voice.file_id}.ogg"
        file = await message.bot.download(message.voice, destination=file_path)

        if not file or not file.exists():
            await status_msg.edit_text("❌ Не удалось скачать голосовое")
            return

        track_info = await recognizer.recognize_from_file(file)
        asyncio.create_task(safe_delete_file(file, delay=5))

        if track_info:
            await status_msg.edit_text(
                recognizer.format_track_info(track_info),
                reply_markup=InlineKeyboards.recognized_track(track_info)
            )
        else:
            await status_msg.edit_text(
                "❌ Не удалось распознать трек.\n"
                "Убедитесь, что в записи чётко слышна музыка."
            )

    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")


async def recognize_video(message: types.Message):
    try:
        status_msg = await message.answer("🎵 Распознаю музыку из видео...")

        file_path = TEMP_DIR / f"video_{message.from_user.id}_{message.video.file_id}.mp4"
        file = await message.bot.download(message.video, destination=file_path)

        if not file or not file.exists():
            await status_msg.edit_text("❌ Не удалось скачать видео")
            return

        await status_msg.edit_text("🎵 Извлекаю аудио и распознаю...")

        track_info = await recognizer.recognize_from_file(file)
        asyncio.create_task(safe_delete_file(file, delay=5))

        if track_info:
            await status_msg.edit_text(
                recognizer.format_track_info(track_info),
                reply_markup=InlineKeyboards.recognized_track(track_info)
            )
        else:
            await status_msg.edit_text(
                "❌ Не удалось распознать музыку из видео.\n"
                "Попробуйте отправить фрагмент с более чёткой музыкой."
            )

    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")


async def recognize_document(message: types.Message):
    try:
        file_name = (message.document.file_name or "").lower()

        audio_ext = ('.mp3', '.m4a', '.wav', '.ogg', '.flac')
        video_ext = ('.mp4', '.mkv', '.avi', '.mov', '.webm')

        if not file_name.endswith(audio_ext + video_ext):
            return

        status_msg = await message.answer("🎵 Распознаю музыку...")

        suffix = Path(file_name).suffix
        file_path = TEMP_DIR / f"doc_{message.from_user.id}_{message.document.file_id}{suffix}"
        file = await message.bot.download(message.document, destination=file_path)

        if not file or not file.exists():
            await status_msg.edit_text("❌ Не удалось скачать файл")
            return

        track_info = await recognizer.recognize_from_file(file)
        asyncio.create_task(safe_delete_file(file, delay=5))

        if track_info:
            await status_msg.edit_text(
                recognizer.format_track_info(track_info),
                reply_markup=InlineKeyboards.recognized_track(track_info)
            )
        else:
            await status_msg.edit_text("❌ Не удалось распознать музыку из файла.")

    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")


def register(dp: Dispatcher):
    dp.register_message_handler(recognize_audio, content_types=['audio'])
    dp.register_message_handler(recognize_voice, content_types=['voice'])
    dp.register_message_handler(recognize_video, content_types=['video'])
    dp.register_message_handler(recognize_document, content_types=['document'])
