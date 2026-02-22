from aiogram import types
from aiogram.dispatcher import Dispatcher
from services import MusicRecognizer
from keyboards.inline import InlineKeyboards
from utils.helpers import safe_delete_file
from config import TEMP_DIR
import asyncio
from pathlib import Path

recognizer = MusicRecognizer()


async def recognize_audio(message: types.Message):
    """Распознавание загруженного аудио"""
    try:
        status_msg = await message.answer("🎵 Распознаю трек...")
        
        # Скачивание файла
        file = await message.bot.download(
            message.audio,
            destination=TEMP_DIR / f"audio_{message.from_user.id}_{message.audio.file_id}.mp3"
        )
        
        if not file:
            await status_msg.edit_text("❌ Не удалось скачать аудио")
            return
        
        # Распознавание
        track_info = await recognizer.recognize_from_file(file)
        
        # Удаление временного файла
        asyncio.create_task(safe_delete_file(file, delay=5))
        
        if track_info:
            # Форматирование информации
            info_text = recognizer.format_track_info(track_info)
            
            await status_msg.edit_text(
                info_text,
                reply_markup=InlineKeyboards.recognized_track(track_info)
            )
        else:
            await status_msg.edit_text(
                "❌ Не удалось распознать трек.\n"
                "Попробуйте загрузить более качественный фрагмент."
            )
    
    except Exception as e:
        await message.answer(f"❌ Ошибка распознавания: {str(e)}")


async def recognize_voice(message: types.Message):
    """Распознавание голосового сообщения"""
    try:
        status_msg = await message.answer("🎵 Распознаю музыку из голосового...")
        
        # Скачивание голосового
        file = await message.bot.download(
            message.voice,
            destination=TEMP_DIR / f"voice_{message.from_user.id}_{message.voice.file_id}.ogg"
        )
        
        if not file:
            await status_msg.edit_text("❌ Не удалось скачать голосовое")
            return
        
        # Распознавание
        track_info = await recognizer.recognize_from_file(file)
        
        # Удаление
        asyncio.create_task(safe_delete_file(file, delay=5))
        
        if track_info:
            info_text = recognizer.format_track_info(track_info)
            
            await status_msg.edit_text(
                info_text,
                reply_markup=InlineKeyboards.recognized_track(track_info)
            )
        else:
            await status_msg.edit_text(
                "❌ Не удалось распознать трек.\n"
                "Убедитесь, что в записи чётко слышна музыка."
            )
    
    except Exception as e:
        await message.answer(f"❌ Ошибка: {str(e)}")


async def recognize_video(message: types.Message):
    """Распознавание музыки из видео"""
    try:
        status_msg = await message.answer("🎵 Распознаю музыку из видео...")
        
        # Скачивание видео
        file = await message.bot.download(
            message.video,
            destination=TEMP_DIR / f"video_{message.from_user.id}_{message.video.file_id}.mp4"
        )
        
        if not file:
            await status_msg.edit_text("❌ Не удалось скачать видео")
            return
        
        await status_msg.edit_text("🎵 Извлекаю аудио и распознаю...")
        
        # Распознавание
        track_info = await recognizer.recognize_from_file(file)
        
        # Удаление
        asyncio.create_task(safe_delete_file(file, delay=5))
        
        if track_info:
            info_text = recognizer.format_track_info(track_info)
            
            await status_msg.edit_text(
                info_text,
                reply_markup=InlineKeyboards.recognized_track(track_info)
            )
        else:
            await status_msg.edit_text(
                "❌ Не удалось распознать музыку из видео.\n"
                "Попробуйте отправить фрагмент с более чёткой музыкой."
            )
    
    except Exception as e:
        await message.answer(f"❌ Ошибка: {str(e)}")


async def recognize_document(message: types.Message):
    """Распознавание из документа (аудио/видео файл)"""
    try:
        # Проверка расширения
        file_name = message.document.file_name.lower() if message.document.file_name else ""
        
        audio_extensions = ['.mp3', '.m4a', '.wav', '.ogg', '.flac']
        video_extensions = ['.mp4', '.mkv', '.avi', '.mov', '.webm']
        
        is_audio = any(file_name.endswith(ext) for ext in audio_extensions)
        is_video = any(file_name.endswith(ext) for ext in video_extensions)
        
        if not (is_audio or is_video):
            return  # Не обрабатываем другие документы
        
        status_msg = await message.answer("🎵 Распознаю музыку...")
        
        # Скачивание
        file_path = TEMP_DIR / f"doc_{message.from_user.id}_{message.document.file_id}{Path(file_name).suffix}"
        file = await message.bot.download(
            message.document,
            destination=file_path
        )
        
        if not file:
            await status_msg.edit_text("❌ Не удалось скачать файл")
            return
        
        # Распознавание
        track_info = await recognizer.recognize_from_file(file)
        
        # Удаление
        asyncio.create_task(safe_delete_file(file, delay=5))
        
        if track_info:
            info_text = recognizer.format_track_info(track_info)
            
            await status_msg.edit_text(
                info_text,
                reply_markup=InlineKeyboards.recognized_track(track_info)
            )
        else:
            await status_msg.edit_text(
                "❌ Не удалось распознать музыку из файла."
            )
    
    except Exception as e:
        await message.answer(f"❌ Ошибка: {str(e)}")


def register(dp: Dispatcher):
    dp.register_message_handler(recognize_audio, content_types=[types.ContentTypes.AUDIO])
    dp.register_message_handler(recognize_voice, content_types=[types.ContentTypes.VOICE])
    dp.register_message_handler(recognize_video, content_types=[types.ContentTypes.VIDEO])
    dp.register_message_handler(recognize_document, content_types=[types.ContentTypes.DOCUMENT])
