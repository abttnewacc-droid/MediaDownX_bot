import asyncio
from pathlib import Path
from typing import Optional, Dict
from shazamio import Shazam
from config import RECOGNITION_TIMEOUT


class MusicRecognizer:
    """Сервис распознавания музыки через Shazam API"""
    
    def __init__(self):
        self.shazam = Shazam()
    
    async def recognize_from_file(self, filepath: Path) -> Optional[Dict]:
        """Распознавание музыки из файла"""
        try:
            # Timeout для распознавания
            result = await asyncio.wait_for(
                self.shazam.recognize(str(filepath)),
                timeout=RECOGNITION_TIMEOUT
            )
            
            if not result or 'track' not in result:
                return None
            
            track_info = self._parse_shazam_response(result)
            return track_info
        
        except asyncio.TimeoutError:
            print("Recognition timeout")
            return None
        except Exception as e:
            print(f"Recognition error: {e}")
            return None
    
    async def recognize_from_url(self, url: str) -> Optional[Dict]:
        """Распознавание музыки из видео по URL"""
        from services.downloader import MediaDownloader
        from utils.helpers import safe_delete_file
        
        try:
            # Скачивание аудио из видео
            downloader = MediaDownloader()
            audio_file = await downloader.download_video(
                url, 
                audio_only=True
            )
            
            if not audio_file or not audio_file.exists():
                return None
            
            # Распознавание
            result = await self.recognize_from_file(audio_file)
            
            # Удаление временного файла
            asyncio.create_task(safe_delete_file(audio_file, delay=5))
            
            return result
        
        except Exception as e:
            print(f"URL recognition error: {e}")
            return None
    
    def _parse_shazam_response(self, data: dict) -> Dict:
        """Парсинг ответа Shazam"""
        track = data.get('track', {})
        
        return {
            'title': track.get('title', 'Unknown'),
            'artist': track.get('subtitle', 'Unknown Artist'),
            'album': track.get('sections', [{}])[0].get('metadata', [{}])[0].get('text') if track.get('sections') else None,
            'genre': track.get('genres', {}).get('primary', 'Unknown'),
            'release_date': self._extract_release_date(track),
            'cover_url': self._extract_cover_url(track),
            'shazam_url': track.get('url'),
            'apple_music_url': self._extract_apple_music_url(track),
            'youtube_url': self._extract_youtube_url(track),
            'isrc': track.get('isrc'),
        }
    
    def _extract_release_date(self, track: dict) -> Optional[str]:
        """Извлечение даты релиза"""
        sections = track.get('sections', [])
        for section in sections:
            metadata = section.get('metadata', [])
            for meta in metadata:
                if meta.get('title') == 'Released':
                    return meta.get('text')
        return None
    
    def _extract_cover_url(self, track: dict) -> Optional[str]:
        """Извлечение URL обложки"""
        images = track.get('images', {})
        
        # Приоритет качеству
        for quality in ['coverarthq', 'coverart', 'background']:
            if quality in images:
                return images[quality]
        
        return None
    
    def _extract_apple_music_url(self, track: dict) -> Optional[str]:
        """Извлечение ссылки на Apple Music"""
        hub = track.get('hub', {})
        providers = hub.get('providers', [])
        
        for provider in providers:
            if 'applemusic' in provider.get('type', '').lower():
                actions = provider.get('actions', [])
                if actions:
                    return actions[0].get('uri')
        
        return None
    
    def _extract_youtube_url(self, track: dict) -> Optional[str]:
        """Извлечение ссылки на YouTube"""
        sections = track.get('sections', [])
        
        for section in sections:
            if section.get('type') == 'VIDEO':
                items = section.get('items', [])
                if items:
                    return items[0].get('actions', [{}])[0].get('uri')
        
        return None
    
    async def search_track(self, query: str, limit: int = 10) -> list[Dict]:
        """Поиск треков по названию"""
        try:
            results = await self.shazam.search_track(
                query=query,
                limit=limit
            )
            
            if not results or 'tracks' not in results:
                return []
            
            tracks = []
            for hit in results['tracks'].get('hits', []):
                track = hit.get('track', {})
                tracks.append({
                    'title': track.get('title', 'Unknown'),
                    'artist': track.get('subtitle', 'Unknown Artist'),
                    'cover_url': self._extract_cover_url(track),
                    'shazam_url': track.get('url'),
                    'key': track.get('key'),  # ID для скачивания
                })
            
            return tracks
        
        except Exception as e:
            print(f"Search error: {e}")
            return []
    
    def format_track_info(self, track_info: Dict) -> str:
        """Форматирование информации о треке для вывода"""
        text = f"🎵 <b>{track_info['title']}</b>\n"
        text += f"👤 {track_info['artist']}\n"
        
        if track_info.get('album'):
            text += f"💿 {track_info['album']}\n"
        
        if track_info.get('genre'):
            text += f"🎼 {track_info['genre']}\n"
        
        if track_info.get('release_date'):
            text += f"📅 {track_info['release_date']}\n"
        
        return text
