from aiogram import types
from aiogram.dispatcher import Dispatcher
from keyboards.inline import InlineKeyboards


async def cmd_start(message: types.Message):
    welcome_text = """
🎬 <b>Добро пожаловать в MediaDownX!</b>

Я помогу тебе скачать медиа с максимальным качеством:

📹 <b>Видео:</b>
• YouTube (включая Shorts)
• Instagram (Reels, Posts, Stories)
• TikTok
• Twitter / X
• Pinterest
• Любые прямые ссылки

🎵 <b>Аудио:</b>
• Скачивание из видео
• Поиск по названию
• Распознавание музыки (Shazam)
• Метаданные и обложки

🖼 <b>Изображения:</b>
• Оригинальное качество
• Без сжатия Telegram

<b>Как использовать:</b>
1. Отправь ссылку на видео/изображение
2. Выбери нужное качество
3. Получи файл без сжатия!

Или напиши название песни для поиска 🎶
"""
    await message.answer(welcome_text, reply_markup=InlineKeyboards.main_menu())


async def cmd_help(message: types.Message):
    help_text = """
📖 <b>Подробная инструкция:</b>

<b>1️⃣ Скачивание видео:</b>
• Отправь ссылку на видео
• Выбери качество (144p - 4K)
• Получи видео без сжатия

<b>2️⃣ Скачивание аудио:</b>
• Отправь ссылку на видео и выбери "Только аудио"
• Или напиши: <code>Imagine Dragons Believer</code>
• Выбери нужный трек из списка

<b>3️⃣ Распознавание музыки:</b>
• Отправь аудио/голосовое сообщение
• Или отправь видео для распознавания
• Получи информацию о треке + возможность скачать

<b>4️⃣ Изображения:</b>
• Отправь ссылку на пост Instagram/Pinterest
• Получи оригинал без сжатия
"""
    await message.answer(help_text)


async def callback_help(callback: types.CallbackQuery):
    await callback.message.delete()
    await cmd_help(callback.message)
    await callback.answer()


async def callback_about(callback: types.CallbackQuery):
    about_text = """
🤖 <b>MediaDownX Bot</b>

<b>Версия:</b> 1.0.0
<b>Разработчик:</b> @AbdullohBazhov

<b>Технологии:</b>
• Python + aiogram 2.25.2
• yt-dlp
• Shazam (shazamio)
• FFmpeg

<b>Возможности:</b>
✨ Скачивание видео до 4K
✨ Аудио с метаданными
✨ Распознавание музыки
✨ Оригинальное качество изображений
✨ Без ограничений
"""
    await callback.message.edit_text(about_text, reply_markup=InlineKeyboards.main_menu())
    await callback.answer()


def register(dp: Dispatcher):
    dp.register_message_handler(cmd_start, commands=["start"])
    dp.register_message_handler(cmd_help, commands=["help"])
    dp.register_callback_query_handler(callback_help, lambda c: c.data == "help")
    dp.register_callback_query_handler(callback_about, lambda c: c.data == "about")
