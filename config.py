import os
from pathlib import Path

# Telegram
BOT_TOKEN = "8575578221:AAERcDMRuNFk7OmHg4e36m7hjj-1ocphK6Q"
ADMIN_ID = 7734272036

# Пути
BASE_DIR = Path(__file__).parent
TEMP_DIR = BASE_DIR / "temp"
TEMP_DIR.mkdir(exist_ok=True)

# Ограничения
MAX_FILE_SIZE = 2000 * 1024 * 1024  # 2GB (лимит Telegram)
MAX_VIDEO_DURATION = 3600  # 1 час
FLOOD_LIMIT = 5  # сообщений в минуту

# yt-dlp настройки
YT_DLP_OPTIONS = {
    'quiet': True,
    'no_warnings': True,
    'extract_flat': False,
    'socket_timeout': 30,
}

# Поддерживаемые качества видео
VIDEO_QUALITIES = [
    ('144p', '144'),
    ('240p', '240'),
    ('360p', '360'),
    ('480p', '480'),
    ('720p', '720'),
    ('1080p', '1080'),
    ('1440p', '1440'),
    ('4K', '2160'),
]

# Форматы аудио
AUDIO_FORMATS = ['mp3', 'm4a', 'wav']
DEFAULT_AUDIO_FORMAT = 'mp3'
AUDIO_BITRATE = '320k'

# Таймауты
DOWNLOAD_TIMEOUT = 600  # 10 минут
RECOGNITION_TIMEOUT = 30  # 30 секунд
