from pathlib import Path

# ─── TELEGRAM ─────────────────────────────────────────────────────────
BOT_TOKEN = "8575578221:AAERcDMRuNFk7OmHg4e36m7hjj-1ocphK6Q"
ADMIN_ID = 7734272036

# ─── PATHS ────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent
TEMP_DIR = BASE_DIR / "temp"
TEMP_DIR.mkdir(parents=True, exist_ok=True)

# ─── LIMITS ───────────────────────────────────────────────────────────
MAX_FILE_SIZE = 2 * 1024 * 1024 * 1024      # 2GB (Telegram hard limit)
MAX_VIDEO_DURATION = 2 * 60 * 60             # 2 часа
FLOOD_LIMIT = 5                              # сообщений в минуту

# ─── YT-DLP (FIXED FOR SHORTS / PINTEREST / INSTA) ────────────────────
YT_DLP_OPTIONS = {
    "quiet": True,
    "no_warnings": True,
    "ignoreerrors": False,
    "noplaylist": True,
    "extract_flat": False,

    # ключевое
    "force_ipv4": True,
    "retries": 10,
    "fragment_retries": 10,
    "socket_timeout": 60,

    # bypass для Instagram / Pinterest / Shorts
    "http_headers": {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/122.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "en-US,en;q=0.9",
    },

    # cookies support (на будущее, не ломает если файла нет)
    "cookiefile": None,
}

# ─── VIDEO QUALITIES (REFERENCE ONLY) ─────────────────────────────────
VIDEO_QUALITIES = [
    ("144p", 144),
    ("240p", 240),
    ("360p", 360),
    ("480p", 480),
    ("720p", 720),
    ("1080p", 1080),
    ("1440p", 1440),
    ("2160p", 2160),  # 4K
]

# ─── AUDIO ────────────────────────────────────────────────────────────
AUDIO_FORMATS = ["mp3", "m4a", "wav"]
DEFAULT_AUDIO_FORMAT = "mp3"
AUDIO_BITRATE = "320k"

# ─── TIMEOUTS ─────────────────────────────────────────────────────────
DOWNLOAD_TIMEOUT = 15 * 60       # 15 минут (реально нужно для 4K)
RECOGNITION_TIMEOUT = 40         # Shazam
