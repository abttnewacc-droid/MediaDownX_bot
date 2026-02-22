from aiogram import types
from aiogram.dispatcher import Dispatcher
from services import MusicRecognizer, MediaDownloader, AudioProcessor
from keyboards.inline import InlineKeyboards
from utils.helpers import safe_delete_file
import asyncio
from aiogram.types import FSInputFile

recognizer = MusicRecognizer()
downloader = MediaDownloader()
audio_processor = AudioProcessor()

# Хранилище результатов поиска для каждого пользователя
user_search_results = {}


async def search_audio(message: types.Message, query: str):
    """Поиск аудио по запросу"""
    try:
        status_msg = await message.answer("🔍 Ищу треки...")
        
        # Поиск через Shazam
        tracks = await recognizer.search_track(query, limit=10)
        
        if not tracks:
            await status_msg.edit_text(
                f"❌ Ничего не найдено по запросу: <b>{query}</b>\n\n"
                "Попробуйте изменить запрос или использовать другое название."
            )
            return
        
        # Сохранение результатов для пользователя
        user_id = message.from_user.id
        user_search_results[user_id] = tracks
        
        # Формирование списка треков
        result_text = f"🎵 <b>Найдено {len(tracks)} треков:</b>\n\n"
        
        for idx, track in enumerate(tracks, 1):
            result_text += f"{idx}. <b>{track['title']}</b>\n"
            result_text += f"   👤 {track['artist']}\n\n"
        
        result_text += "Выберите трек для скачивания:"
        
        await status_msg.edit_text(
            result_text,
            reply_markup=InlineKeyboards.audio_search_results(tracks)
        )
    
    except Exception as e:
        await message.answer(f"❌ Ошибка поиска: {str(e)}")


async def callback_download_track(callback: types.CallbackQuery):
    """Callback скачивания трека из результатов поиска"""
    try:
        # Парсинг индекса трека
        track_idx = int(callback.data.split(":")[1])
        user_id = callback.from_user.id
        
        # Получение результатов поиска пользователя
        if user_id not in user_search_results:
            await callback.answer("❌ Результаты поиска устарели. Выполните поиск заново.", show_alert=True)
            return
        
        tracks = user_search_results[user_id]
        
        if track_idx >= len(tracks):
            await callback.answer("❌ Неверный трек", show_alert=True)
            return
        
        track = tracks[track_idx]
        
        await callback.message.edit_text(
            f"⏳ Скачиваю трек:\n<b>{track['title']}</b> - {track['artist']}"
        )
        
        # Поиск и скачивание через YouTube
        search_query = f"{track['artist']} {track['title']} audio"
        youtube_url = f"ytsearch1:{search_query}"
        
        # Загрузка аудио
        audio_file = await downloader.download_video(
            youtube_url,
            audio_only=True
        )
        
        if audio_file and audio_file.exists():
            await callback.message.edit_text("🎨 Добавляю метаданные...")
            
            # Добавление метаданных
            metadata = {
                'title': track['title'],
                'artist': track['artist'],
            }
            
            await audio_processor.add_metadata(
                audio_file,
                metadata,
                cover_url=track.get('cover_url')
            )
            
            await callback.message.edit_text("📤 Отправляю трек...")
            
            # Отправка аудио
            await callback.message.answer_audio(
                FSInputFile(audio_file),
                title=track['title'],
                performer=track['artist'],
                caption=f"🎵 <b>{track['title']}</b>\n👤 {track['artist']}"
            )
            
            await callback.message.delete()
            
            # Удаление временного файла
            asyncio.create_task(safe_delete_file(audio_file, delay=30))
        else:
            await callback.message.edit_text(
                "❌ Не удалось скачать трек.\n"
                "Попробуйте другой вариант из списка."
            )
        
        await callback.answer()
    
    except Exception as e:
        await callback.message.edit_text(f"❌ Ошибка: {str(e)}")
        await callback.answer()


async def callback_download_recognized(callback: types.CallbackQuery):
    """Callback скачивания распознанного трека"""
    try:
        # Извлечение названия трека
        track_title = callback.data.split(":", 1)[1]
        
        await callback.message.edit_text(f"⏳ Скачиваю: <b>{track_title}</b>")
        
        # Поиск на YouTube
        youtube_url = f"ytsearch1:{track_title}"
        
        # Загрузка
        audio_file = await downloader.download_video(
            youtube_url,
            audio_only=True
        )
        
        if audio_file and audio_file.exists():
            await callback.message.edit_text("📤 Отправляю...")
            
            # Отправка
            await callback.message.answer_audio(
                FSInputFile(audio_file),
                caption=f"🎵 {track_title}"
            )
            
            await callback.message.delete()
            
            # Удаление
            asyncio.create_task(safe_delete_file(audio_file, delay=30))
        else:
            await callback.message.edit_text("❌ Не удалось скачать трек")
        
        await callback.answer()
    
    except Exception as e:
        await callback.message.edit_text(f"❌ Ошибка: {str(e)}")
        await callback.answer()


def register(dp: Dispatcher):
    dp.register_callback_query_handler(callback_download_track, lambda c: c.data.startswith("download_track:"))
    dp.register_callback_query_handler(callback_download_recognized, lambda c: c.data.startswith("download_recognized:"))
