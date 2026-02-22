# utils/validators.py
import re
from typing import Optional


class URLValidator:
    """Валидатор URL для поддерживаемых платформ"""

    # максимально либеральные паттерны, чтобы yt-dlp сам решал
    PATTERNS = {
        'youtube': [
            r'youtu\.be\/',
            r'youtube\.com\/',
        ],
        'instagram': [
            r'instagram\.com\/',
        ],
        'tiktok': [
            r'tiktok\.com\/',
        ],
        'twitter': [
            r'(?:twitter|x)\.com\/',
        ],
        'pinterest': [
            r'pinterest\.(com|ru)\/',
        ],
    }

    MEDIA_EXTENSIONS = (
        '.mp4', '.webm', '.mkv', '.mov',
        '.jpg', '.jpeg', '.png', '.gif', '.webp',
        '.mp3', '.m4a', '.wav', '.ogg', '.flac'
    )

    @classmethod
    def is_valid_url(cls, url: str) -> bool:
        if not url or not url.startswith(('http://', 'https://')):
            return False

        url_l = url.lower()

        # прямая ссылка на файл
        if any(url_l.endswith(ext) for ext in cls.MEDIA_EXTENSIONS):
            return True

        # соцсети / платформы
        for patterns in cls.PATTERNS.values():
            for pattern in patterns:
                if re.search(pattern, url_l):
                    return True

        return False

    @classmethod
    def detect_platform(cls, url: str) -> Optional[str]:
        url_l = url.lower()

        for platform, patterns in cls.PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, url_l):
                    return platform

        if url.startswith(('http://', 'https://')):
            return 'direct'

        return None

    @classmethod
    def is_image_url(cls, url: str) -> bool:
        url_l = url.lower()
        return any(url_l.endswith(ext) for ext in ('.jpg', '.jpeg', '.png', '.gif', '.webp'))

    @classmethod
    def is_video_url(cls, url: str) -> bool:
        url_l = url.lower()
        return any(url_l.endswith(ext) for ext in ('.mp4', '.webm', '.mov', '.avi', '.mkv'))

    @classmethod
    def is_audio_url(cls, url: str) -> bool:
        url_l = url.lower()
        return any(url_l.endswith(ext) for ext in ('.mp3', '.m4a', '.wav', '.ogg', '.flac'))
