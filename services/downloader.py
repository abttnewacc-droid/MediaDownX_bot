import asyncio
import yt_dlp
from pathlib import Path
from typing import Optional, Dict, List
from config import TEMP_DIR, YT_DLP_OPTIONS, MAX_FILE_SIZE
from utils.helpers import clean_filename


class MediaDownloader:
    """Сервис загрузки медиа через yt-dlp"""
    
    def __init__(self):
        self.temp_dir = TEMP_DIR
    
    async def get_video_info(self, url: str) -> Optional[Dict]:
        """Получение информации о видео"""
        try:
            ydl_opts = {
                **YT_DLP_OPTIONS,
                'skip_download': True,
            }
            
            loop = asyncio.get_event_loop()
            info = await loop.run_in_executor(
                None,
                lambda: self._extract_info(url, ydl_opts)
            )
            
            return info
        
        except Exception as e:
            print(f"Error getting video info: {e}")
            return None
    
    def _extract_info(self, url: str, opts: dict) -> dict:
        """Синхронное извлечение информации"""
        with yt_dlp.YoutubeDL(opts) as ydl:
            return ydl.extract_info(url, download=False)
    
    async def get_available_qualities(self, url: str) -> List[Dict]:
        """Получение доступных качеств видео"""
        info = await self.get_video_info(url)
        if not info:
            return []
        
        formats = info.get('formats', [])
        qualities = []
        seen_heights = set()
        
        for fmt in formats:
            height = fmt.get('height')
            if not height or height in seen_heights:
                continue
            
            # Только видео с аудио или отдельные видео потоки
            if fmt.get('vcodec') != 'none':
                qualities.append({
                    'height': height,
                    'format_id': fmt.get('format_id'),
                    'ext': fmt.get('ext', 'mp4'),
                    'filesize': fmt.get('filesize', 0),
                    'fps': fmt.get('fps', 30),
                })
                seen_heights.add(height)
        
        # Сортировка по качеству
        qualities.sort(key=lambda x: x['height'])
        return qualities
    
    async def download_video(
        self, 
        url: str, 
        quality: str = 'best',
        audio_only: bool = False,
        progress_callback=None
    ) -> Optional[Path]:
        """Загрузка видео"""
        try:
            filename = f"{self.temp_dir}/{self._generate_filename()}"
            
            if audio_only:
                ydl_opts = {
                    **YT_DLP_OPTIONS,
                    'format': 'bestaudio/best',
                    'outtmpl': filename,
                    'postprocessors': [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                        'preferredquality': '320',
                    }],
                }
            else:
                # Формат для видео с аудио
                if quality == 'best':
                    format_selector = 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'
                else:
                    format_selector = f'bestvideo[height<={quality}][ext=mp4]+bestaudio[ext=m4a]/best[height<={quality}][ext=mp4]/best'
                
                ydl_opts = {
                    **YT_DLP_OPTIONS,
                    'format': format_selector,
                    'outtmpl': filename,
                    'merge_output_format': 'mp4',
                }
            
            # Progress hook
            if progress_callback:
                ydl_opts['progress_hooks'] = [
                    lambda d: asyncio.create_task(progress_callback(d))
                ]
            
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: self._download(url, ydl_opts)
            )
            
            # Поиск скачанного файла
            downloaded_file = self._find_downloaded_file(filename)
            return downloaded_file
        
        except Exception as e:
            print(f"Download error: {e}")
            return None
    
    def _download(self, url: str, opts: dict):
        """Синхронная загрузка"""
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([url])
    
    def _find_downloaded_file(self, base_filename: str) -> Optional[Path]:
        """Поиск скачанного файла"""
        base_path = Path(base_filename)
        
        # Проверка точного совпадения
        if base_path.exists():
            return base_path
        
        # Поиск с разными расширениями
        for ext in ['.mp4', '.webm', '.mkv', '.mp3', '.m4a']:
            file_path = base_path.with_suffix(ext)
            if file_path.exists():
                return file_path
        
        # Поиск по паттерну
        parent_dir = base_path.parent
        filename_pattern = base_path.stem
        
        for file in parent_dir.glob(f"{filename_pattern}*"):
            if file.is_file():
                return file
        
        return None
    
    async def download_image(self, url: str) -> Optional[Path]:
        """Загрузка изображения"""
        try:
            filename = f"{self.temp_dir}/{self._generate_filename()}.jpg"
            
            ydl_opts = {
                **YT_DLP_OPTIONS,
                'outtmpl': filename,
            }
            
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: self._download(url, ydl_opts)
            )
            
            downloaded_file = self._find_downloaded_file(filename)
            return downloaded_file
        
        except Exception as e:
            print(f"Image download error: {e}")
            return None
    
    async def download_direct_url(self, url: str) -> Optional[Path]:
        """Загрузка по прямой ссылке"""
        import aiohttp
        import aiofiles
        
        try:
            filename = f"{self.temp_dir}/{self._generate_filename()}"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        # Определение расширения
                        content_type = response.headers.get('Content-Type', '')
                        ext = self._get_extension_from_content_type(content_type)
                        
                        if not ext:
                            # Попытка извлечь из URL
                            ext = Path(url).suffix or '.bin'
                        
                        filepath = Path(f"{filename}{ext}")
                        
                        async with aiofiles.open(filepath, 'wb') as f:
                            await f.write(await response.read())
                        
                        return filepath
            
            return None
        
        except Exception as e:
            print(f"Direct download error: {e}")
            return None
    
    def _get_extension_from_content_type(self, content_type: str) -> str:
        """Определение расширения по Content-Type"""
        mapping = {
            'video/mp4': '.mp4',
            'video/webm': '.webm',
            'image/jpeg': '.jpg',
            'image/png': '.png',
            'image/gif': '.gif',
            'audio/mpeg': '.mp3',
            'audio/mp4': '.m4a',
        }
        return mapping.get(content_type, '')
    
    def _generate_filename(self) -> str:
        """Генерация уникального имени файла"""
        import time
        import random
        timestamp = int(time.time() * 1000)
        random_suffix = random.randint(1000, 9999)
        return f"media_{timestamp}_{random_suffix}"
    
    async def get_thumbnail(self, url: str) -> Optional[str]:
        """Получение URL превью видео"""
        info = await self.get_video_info(url)
        if not info:
            return None
        
        return info.get('thumbnail')
