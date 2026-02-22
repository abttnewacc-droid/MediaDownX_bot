import re
from typing import Optional

class URLValidator:
    """Валидатор URL для поддерживаемых платформ"""
    
    PATTERNS = {
        'youtube': [
            r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/shorts\/)([a-zA-Z0-9_-]{11})',
        ],
        'instagram': [
            r'instagram\.com\/(p|reel|stories|tv)\/([a-zA-Z0-9_-]+)',
        ],
        'tiktok': [
            r'tiktok\.com\/.*\/video\/(\d+)',
            r'vm\.tiktok\.com\/([a-zA-Z0-9]+)',
        ],
        'twitter': [
            r'(?:twitter|x)\.com\/\w+\/status\/(\d+)',
        ],
        'pinterest': [
            r'pinterest\.com\/pin\/(\d+)',
        ],
    }
    
    @classmethod
    def is_valid_url(cls, url: str) -> bool:
        """Проверка валидности URL"""
        if not url:
            return False
        
        # Проверка на прямую ссылку на медиа
        if url.startswith(('http://', 'https://')):
            if any(ext in url.lower() for ext in ['.mp4', '.webm', '.jpg', '.jpeg', '.png', '.gif', '.mp3', '.m4a']):
                return True
        
        # Проверка паттернов платформ
        for platform, patterns in cls.PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, url, re.IGNORECASE):
                    return True
        
        return False
    
    @classmethod
    def detect_platform(cls, url: str) -> Optional[str]:
        """Определение платформы по URL"""
        for platform, patterns in cls.PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, url, re.IGNORECASE):
                    return platform
        
        # Прямая ссылка на медиа
        if url.startswith(('http://', 'https://')):
            return 'direct'
        
        return None
    
    @classmethod
    def is_image_url(cls, url: str) -> bool:
        """Проверка является ли URL изображением"""
        return any(ext in url.lower() for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp'])
    
    @classmethod
    def is_video_url(cls, url: str) -> bool:
        """Проверка является ли URL видео"""
        return any(ext in url.lower() for ext in ['.mp4', '.webm', '.mov', '.avi', '.mkv'])
    
    @classmethod
    def is_audio_url(cls, url: str) -> bool:
        """Проверка является ли URL аудио"""
        return any(ext in url.lower() for ext in ['.mp3', '.m4a', '.wav', '.ogg', '.flac'])
