from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import List, Dict


class InlineKeyboards:
    """Фабрика inline клавиатур"""
    
    @staticmethod
    def video_qualities(qualities: List[Dict], url: str) -> InlineKeyboardMarkup:
        """Клавиатура выбора качества видео"""
        keyboard = InlineKeyboardMarkup(row_width=2)
        
        # Кнопки качества (по 2 в ряд)
        for quality in qualities:
            height = quality['height']
            quality_label = f"{height}p"
            
            # 4K обозначение
            if height >= 2160:
                quality_label = "4K"
            elif height >= 1440:
                quality_label = "1440p"
            
            keyboard.insert(
                InlineKeyboardButton(
                    text=f"📹 {quality_label}",
                    callback_data=f"video:{height}:{url}"
                )
            )
        
        # Кнопка "Только аудио"
        keyboard.row()
        keyboard.add(
            InlineKeyboardButton(
                text="🎵 Только аудио",
                callback_data=f"audio_only:{url}"
            )
        )
        
        # Кнопка "Лучшее качество"
        keyboard.add(
            InlineKeyboardButton(
                text="⭐ Лучшее качество (видео+аудио)",
                callback_data=f"video:best:{url}"
            )
        )
        
        return keyboard
    
    @staticmethod
    def audio_search_results(tracks: List[Dict]) -> InlineKeyboardMarkup:
        """Клавиатура результатов поиска аудио"""
        keyboard = InlineKeyboardMarkup(row_width=1)
        
        for idx, track in enumerate(tracks, 1):
            title = track['title'][:30]  # Обрезка длинных названий
            artist = track['artist'][:20]
            
            keyboard.add(
                InlineKeyboardButton(
                    text=f"{idx}. {title} - {artist}",
                    callback_data=f"download_track:{idx-1}"
                )
            )
        
        return keyboard
    
    @staticmethod
    def recognized_track(track_info: Dict) -> InlineKeyboardMarkup:
        """Клавиатура для распознанного трека"""
        keyboard = InlineKeyboardMarkup(row_width=1)
        
        # Кнопка скачивания
        keyboard.add(
            InlineKeyboardButton(
                text="⬇️ Скачать трек",
                callback_data=f"download_recognized:{track_info.get('title', 'track')}"
            )
        )
        
        # Ссылки на стриминги
        if track_info.get('apple_music_url'):
            keyboard.add(
                InlineKeyboardButton(
                    text="🍎 Apple Music",
                    url=track_info['apple_music_url']
                )
            )
        
        if track_info.get('youtube_url'):
            keyboard.add(
                InlineKeyboardButton(
                    text="▶️ YouTube",
                    url=track_info['youtube_url']
                )
            )
        
        if track_info.get('shazam_url'):
            keyboard.add(
                InlineKeyboardButton(
                    text="🔵 Shazam",
                    url=track_info['shazam_url']
                )
            )
        
        return keyboard
    
    @staticmethod
    def audio_format_selection(url: str) -> InlineKeyboardMarkup:
        """Клавиатура выбора формата аудио"""
        keyboard = InlineKeyboardMarkup(row_width=3)
        
        formats = [
            ("MP3", "mp3"),
            ("M4A", "m4a"),
            ("WAV", "wav")
        ]
        
        for label, fmt in formats:
            keyboard.insert(
                InlineKeyboardButton(
                    text=f"🎵 {label}",
                    callback_data=f"audio_format:{fmt}:{url}"
                )
            )
        
        return keyboard
    
    @staticmethod
    def cancel_download() -> InlineKeyboardMarkup:
        """Кнопка отмены загрузки"""
        keyboard = InlineKeyboardMarkup(row_width=1)
        
        keyboard.add(
            InlineKeyboardButton(
                text="❌ Отменить",
                callback_data="cancel_download"
            )
        )
        
        return keyboard
    
    @staticmethod
    def main_menu() -> InlineKeyboardMarkup:
        """Главное меню"""
        keyboard = InlineKeyboardMarkup(row_width=2)
        
        keyboard.add(
            InlineKeyboardButton(
                text="ℹ️ Помощь",
                callback_data="help"
            ),
            InlineKeyboardButton(
                text="👤 О боте",
                callback_data="about"
            )
        )
        
        return keyboard
    
    @staticmethod
    def image_download_options(url: str) -> InlineKeyboardMarkup:
        """Опции загрузки изображений"""
        keyboard = InlineKeyboardMarkup(row_width=1)
        
        keyboard.add(
            InlineKeyboardButton(
                text="📥 Скачать оригинал",
                callback_data=f"image_original:{url}"
            )
        )
        
        return keyboard
