from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import List, Dict
import base64


class InlineKeyboards:
    """Фабрика inline клавиатур (aiogram 2.x, безопасные callback_data)"""

    @staticmethod
    def _encode(data: str) -> str:
        return base64.urlsafe_b64encode(data.encode()).decode()

    @staticmethod
    def video_qualities(qualities: List[Dict], url: str) -> InlineKeyboardMarkup:
        keyboard = InlineKeyboardMarkup(row_width=2)
        encoded_url = InlineKeyboards._encode(url)

        for quality in qualities:
            height = quality['height']
            label = f"{height}p"

            if height >= 2160:
                label = "4K"
            elif height >= 1440:
                label = "1440p"

            keyboard.insert(
                InlineKeyboardButton(
                    text=f"📹 {label}",
                    callback_data=f"video:{height}:{encoded_url}"
                )
            )

        keyboard.add(
            InlineKeyboardButton(
                text="🎵 Только аудио",
                callback_data=f"audio_only:{encoded_url}"
            )
        )

        keyboard.add(
            InlineKeyboardButton(
                text="⭐ Лучшее качество (видео+аудио)",
                callback_data=f"video:best:{encoded_url}"
            )
        )

        return keyboard

    @staticmethod
    def audio_search_results(tracks: List[Dict]) -> InlineKeyboardMarkup:
        keyboard = InlineKeyboardMarkup(row_width=1)

        for idx, track in enumerate(tracks, 1):
            title = track['title'][:30]
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
        keyboard = InlineKeyboardMarkup(row_width=1)

        keyboard.add(
            InlineKeyboardButton(
                text="⬇️ Скачать трек",
                callback_data=f"download_recognized:{track_info.get('title', 'track')}"
            )
        )

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
    def main_menu() -> InlineKeyboardMarkup:
        keyboard = InlineKeyboardMarkup(row_width=2)

        keyboard.add(
            InlineKeyboardButton(text="ℹ️ Помощь", callback_data="help"),
            InlineKeyboardButton(text="👤 О боте", callback_data="about"),
        )

        return keyboard
