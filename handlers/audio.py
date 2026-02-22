from aiogram import types
from aiogram.dispatcher import Dispatcher
from aiogram.types import InputFile
from services import MusicRecognizer, MediaDownloader, AudioProcessor
from keyboards.inline import InlineKeyboards
from utils.helpers import safe_delete_file
import asyncio

recognizer = MusicRecognizer()
downloader = MediaDownloader()
audio_processor = AudioProcessor()

# Хранилище результатов поиска для каждого пользователя
user_search_results: dict[int, list] = {}


async def search_audio(message: types.Message, query: str):
    try:
        status_msg = await message.answer("🔍 Ищу треки...")

        tracks = await recognizer.search_track(query, limit=10)
        if not tracks:
            await status_msg.edit_text(
                f"❌ Ничего не найдено по запросу: <b>{query}</b>\n\n"
                "Попробуйте изменить запрос или использовать другое название."
            )
            return

        user_search_results[message.from_user.id] = tracks

        text = f"🎵 <b>Найдено {len(tracks)} треков:</b>\n\n"
        for i, t in enumerate(tracks, 1):
            text += f"{i}. <b>{t['title']}</b>\n   👤 {t['artist']}\n\n"
        text += "Выберите трек для скачивания:"

        await status_msg.edit_text(
            text,
            reply_markup=InlineKeyboards.audio_search_results(tracks)
        )

    except Exception as e:
        await message.answer(f"❌ Ошибка поиска: {e}")


async def callback_download_track(callback: types.CallbackQuery):
    try:
        user_id = callback.from_user.id
        idx = int(callback.data.split(":")[1])

        if user_id not in user_search_results:
            await callback.answer("❌ Результаты устарели", show_alert=True)
            return

        tracks = user_search_results[user_id]
        if idx >= len(tracks):
            await callback.answer("❌ Неверный трек", show_alert=True)
            return

        track = tracks[idx]
        await callback.message.edit_text(
            f"⏳ Скачиваю:\n<b>{track['title']}</b> — {track['artist']}"
        )

        query = f"{track['artist']} {track['title']} audio"
        audio_file = await downloader.download_video(
            f"ytsearch1:{query}",
            audio_only=True
        )

        if not audio_file or not audio_file.exists():
            await callback.message.edit_text("❌ Не удалось скачать трек")
            return

        await audio_processor.add_metadata(
            audio_file,
            {
                "title": track["title"],
                "artist": track["artist"],
            },
            cover_url=track.get("cover_url")
        )

        await callback.message.answer_audio(
            InputFile(audio_file),
            title=track["title"],
            performer=track["artist"],
            caption=f"🎵 <b>{track['title']}</b>\n👤 {track['artist']}"
        )

        await callback.message.delete()
        asyncio.create_task(safe_delete_file(audio_file, delay=30))
        await callback.answer()

    except Exception as e:
        await callback.message.edit_text(f"❌ Ошибка: {e}")
        await callback.answer()


async def callback_download_recognized(callback: types.CallbackQuery):
    try:
        title = callback.data.replace("download_recognized:", "")
        await callback.message.edit_text(f"⏳ Скачиваю: <b>{title}</b>")

        audio_file = await downloader.download_video(
            f"ytsearch1:{title}",
            audio_only=True
        )

        if not audio_file or not audio_file.exists():
            await callback.message.edit_text("❌ Не удалось скачать трек")
            return

        await callback.message.answer_audio(
            InputFile(audio_file),
            caption=f"🎵 {title}"
        )

        await callback.message.delete()
        asyncio.create_task(safe_delete_file(audio_file, delay=30))
        await callback.answer()

    except Exception as e:
        await callback.message.edit_text(f"❌ Ошибка: {e}")
        await callback.answer()


def register(dp: Dispatcher):
    dp.register_callback_query_handler(
        callback_download_track,
        lambda c: c.data.startswith("download_track:")
    )
    dp.register_callback_query_handler(
        callback_download_recognized,
        lambda c: c.data.startswith("download_recognized:")
    )
