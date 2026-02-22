from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from typing import List, Dict


class InlineKeyboards:
    """Фабрика inline клавиатур"""
    
    @staticmethod
    def video_qualities(qualities: List[Dict], url: str) -> InlineKeyboardMarkup:
        """Клавиатура выбора качества видео"""
        builder = InlineKeyboardBuilder()
        
        # Кнопки качества (по 2 в ряд)
        for quality in qualities:
            height = quality['height']
            quality_label = f"{height}p"
            
            # 4K обозначение
            if height >= 2160:
                quality_label = "4K"
            elif height >= 1440:
                quality_label = "1440p"
            
            builder.button(
                text=f"📹 {quality_label}",
                callback_data=f"video:{height}:{url}"
            )
        
        builder.adjust(2)  # 2 кнопки в ряд
        
        # Кнопка "Только аудио"
        builder.row(
            InlineKeyboardButton(
                text="🎵 Только аудио",
                callback_data=f"audio_only:{url}"
            )
        )
        
        # Кнопка "Лучшее качество"
        builder.row(
            InlineKeyboardButton(
                text="⭐ Лучшее качество (видео+аудио)",
                callback_data=f"video:best:{url}"
            )
        )
        
        return builder.as_markup()
    
    @staticmethod
    def audio_search_results(tracks: List[Dict]) -> InlineKeyboardMarkup:
        """Клавиатура результатов поиска аудио"""
        builder = InlineKeyboardBuilder()
        
        for idx, track in enumerate(tracks, 1):
            title = track['title'][:30]  # Обрезка длинных названий
            artist = track['artist'][:20]
            
            builder.row(
                InlineKeyboardButton(
                    text=f"{idx}. {title} - {artist}",
                    callback_data=f"download_track:{idx-1}"
                )
            )
        
        return builder.as_markup()
    
    @staticmethod
    def recognized_track(track_info: Dict) -> InlineKeyboardMarkup:
        """Клавиатура для распознанного трека"""
        builder = InlineKeyboardBuilder()
        
        # Кнопка скачивания
        builder.row(
            InlineKeyboardButton(
                text="⬇️ Скачать трек",
                callback_data=f"download_recognized:{track_info.get('title', 'track')}"
            )
        )
        
        # Ссылки на стриминги
        if track_info.get('apple_music_url'):
            builder.row(
                InlineKeyboardButton(
                    text="🍎 Apple Music",
                    url=track_info['apple_music_url']
                )
            )
        
        if track_info.get('youtube_url'):
            builder.row(
                InlineKeyboardButton(
                    text="▶️ YouTube",
                    url=track_info['youtube_url']
                )
            )
        
        if track_info.get('shazam_url'):
            builder.row(
                InlineKeyboardButton(
                    text="🔵 Shazam",
                    url=track_info['shazam_url']
                )
            )
        
        return builder.as_markup()
    
    @staticmethod
    def audio_format_selection(url: str) -> InlineKeyboardMarkup:
        """Клавиатура выбора формата аудио"""
        builder = InlineKeyboardBuilder()
        
        formats = [
            ("MP3", "mp3"),
            ("M4A", "m4a"),
            ("WAV", "wav")
        ]
        
        for label, fmt in formats:
            builder.button(
                text=f"🎵 {label}",
                callback_data=f"audio_format:{fmt}:{url}"
            )
        
        builder.adjust(3)  # 3 кнопки в ряд
        
        return builder.as_markup()
    
    @staticmethod
    def cancel_download() -> InlineKeyboardMarkup:
        """Кнопка отмены загрузки"""
        builder = InlineKeyboardBuilder()
        
        builder.row(
            InlineKeyboardButton(
                text="❌ Отменить",
                callback_data="cancel_download"
            )
        )
        
        return builder.as_markup()
    
    @staticmethod
    def main_menu() -> InlineKeyboardMarkup:
        """Главное меню"""
        builder = InlineKeyboardBuilder()
        
        builder.row(
            InlineKeyboardButton(
                text="ℹ️ Помощь",
                callback_data="help"
            )
        )
        
        builder.row(
            InlineKeyboardButton(
                text="👤 О боте",
                callback_data="about"
            )
        )
        
        return builder.as_markup()
    
    @staticmethod
    def image_download_options(url: str) -> InlineKeyboardMarkup:
        """Опции загрузки изображений"""
        builder = InlineKeyboardBuilder()
        
        builder.row(
            InlineKeyboardButton(
                text="📥 Скачать оригинал",
                callback_data=f"image_original:{url}"
            )
        )
        
        return builder.as_markup()
