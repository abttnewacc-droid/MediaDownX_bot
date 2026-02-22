import asyncio
from pathlib import Path
from typing import Optional, Dict, List
from shazamio import Shazam
from config import RECOGNITION_TIMEOUT


class MusicRecognizer:
    """Сервис распознавания музыки через Shazam"""

    def __init__(self):
        # один экземпляр на весь процесс
        self.shazam = Shazam()

    async def recognize_from_file(self, filepath: Path) -> Optional[Dict]:
        """Распознавание музыки из локального файла"""
        try:
            if not filepath.exists():
                return None

            result = await asyncio.wait_for(
                self.shazam.recognize(str(filepath)),
                timeout=RECOGNITION_TIMEOUT,
            )

            if not result or "track" not in result:
                return None

            return self._parse_shazam_response(result)

        except asyncio.TimeoutError:
            return None
        except Exception:
            return None

    async def recognize_from_url(self, url: str) -> Optional[Dict]:
        """Распознавание музыки по ссылке (через временную загрузку аудио)"""
        from services.downloader import MediaDownloader
        from utils.helpers import safe_delete_file

        downloader = MediaDownloader()
        audio_file: Optional[Path] = None

        try:
            audio_file = await downloader.download_video(
                url=url,
                audio_only=True,
            )

            if not audio_file or not audio_file.exists():
                return None

            result = await self.recognize_from_file(audio_file)
            return result

        except Exception:
            return None

        finally:
            if audio_file:
                asyncio.create_task(safe_delete_file(audio_file, delay=5))

    async def search_track(self, query: str, limit: int = 10) -> List[Dict]:
        """Поиск треков по названию"""
        try:
            results = await asyncio.wait_for(
                self.shazam.search_track(query=query, limit=limit),
                timeout=RECOGNITION_TIMEOUT,
            )

            hits = results.get("tracks", {}).get("hits", []) if results else []
            tracks: List[Dict] = []

            for hit in hits:
                track = hit.get("track", {})
                tracks.append({
                    "title": track.get("title", "Unknown"),
                    "artist": track.get("subtitle", "Unknown Artist"),
                    "album": self._extract_album(track),
                    "genre": track.get("genres", {}).get("primary"),
                    "release_date": self._extract_release_date(track),
                    "cover_url": self._extract_cover_url(track),
                    "shazam_url": track.get("url"),
                    "apple_music_url": self._extract_apple_music_url(track),
                    "youtube_url": self._extract_youtube_url(track),
                    "isrc": track.get("isrc"),
                })

            return tracks

        except asyncio.TimeoutError:
            return []
        except Exception:
            return []

    def format_track_info(self, track_info: Dict) -> str:
        """Форматирование информации о треке"""
        lines = [
            f"🎵 <b>{track_info.get('title', 'Unknown')}</b>",
            f"👤 {track_info.get('artist', 'Unknown Artist')}",
        ]

        if track_info.get("album"):
            lines.append(f"💿 {track_info['album']}")
        if track_info.get("genre"):
            lines.append(f"🎼 {track_info['genre']}")
        if track_info.get("release_date"):
            lines.append(f"📅 {track_info['release_date']}")

        return "\n".join(lines)

    # ───── helpers ─────

    def _parse_shazam_response(self, data: dict) -> Dict:
        track = data.get("track", {})
        return {
            "title": track.get("title", "Unknown"),
            "artist": track.get("subtitle", "Unknown Artist"),
            "album": self._extract_album(track),
            "genre": track.get("genres", {}).get("primary"),
            "release_date": self._extract_release_date(track),
            "cover_url": self._extract_cover_url(track),
            "shazam_url": track.get("url"),
            "apple_music_url": self._extract_apple_music_url(track),
            "youtube_url": self._extract_youtube_url(track),
            "isrc": track.get("isrc"),
        }

    def _extract_album(self, track: dict) -> Optional[str]:
        sections = track.get("sections", [])
        for section in sections:
            for meta in section.get("metadata", []):
                if meta.get("title", "").lower() == "album":
                    return meta.get("text")
        return None

    def _extract_release_date(self, track: dict) -> Optional[str]:
        sections = track.get("sections", [])
        for section in sections:
            for meta in section.get("metadata", []):
                if meta.get("title") == "Released":
                    return meta.get("text")
        return None

    def _extract_cover_url(self, track: dict) -> Optional[str]:
        images = track.get("images", {})
        for key in ("coverarthq", "coverart", "background"):
            if images.get(key):
                return images[key]
        return None

    def _extract_apple_music_url(self, track: dict) -> Optional[str]:
        hub = track.get("hub", {})
        for provider in hub.get("providers", []):
            if "apple" in provider.get("type", "").lower():
                actions = provider.get("actions", [])
                if actions:
                    return actions[0].get("uri")
        return None

    def _extract_youtube_url(self, track: dict) -> Optional[str]:
        for section in track.get("sections", []):
            if section.get("type") == "VIDEO":
                items = section.get("items", [])
                if items:
                    return items[0].get("actions", [{}])[0].get("uri")
        return None
