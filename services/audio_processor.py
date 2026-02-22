import asyncio
import aiohttp
import aiofiles
from pathlib import Path
from typing import Optional, Dict
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, TIT2, TPE1, TALB, APIC, TDRC
from mutagen.mp4 import MP4, MP4Cover
from config import TEMP_DIR, AUDIO_BITRATE, DEFAULT_AUDIO_FORMAT


class AudioProcessor:
    """Сервис обработки аудио файлов и метаданных"""
    
    def __init__(self):
        self.temp_dir = TEMP_DIR
    
    async def add_metadata(
        self, 
        filepath: Path, 
        metadata: Dict,
        cover_url: Optional[str] = None
    ) -> bool:
        """Добавление метаданных к аудио файлу"""
        try:
            ext = filepath.suffix.lower()
            
            if ext == '.mp3':
                return await self._add_metadata_mp3(filepath, metadata, cover_url)
            elif ext == '.m4a':
                return await self._add_metadata_m4a(filepath, metadata, cover_url)
            
            return False
        
        except Exception as e:
            print(f"Metadata error: {e}")
            return False
    
    async def _add_metadata_mp3(
        self, 
        filepath: Path, 
        metadata: Dict,
        cover_url: Optional[str]
    ) -> bool:
        """Добавление метаданных к MP3"""
        try:
            # Создание/загрузка ID3 тегов
            try:
                audio = MP3(str(filepath), ID3=ID3)
                audio.add_tags()
            except:
                audio = MP3(str(filepath))
            
            # Добавление тегов
            if metadata.get('title'):
                audio.tags.add(TIT2(encoding=3, text=metadata['title']))
            
            if metadata.get('artist'):
                audio.tags.add(TPE1(encoding=3, text=metadata['artist']))
            
            if metadata.get('album'):
                audio.tags.add(TALB(encoding=3, text=metadata['album']))
            
            if metadata.get('release_date'):
                audio.tags.add(TDRC(encoding=3, text=metadata['release_date']))
            
            # Добавление обложки
            if cover_url:
                cover_data = await self._download_cover(cover_url)
                if cover_data:
                    audio.tags.add(
                        APIC(
                            encoding=3,
                            mime='image/jpeg',
                            type=3,  # Cover (front)
                            desc='Cover',
                            data=cover_data
                        )
                    )
            
            audio.save()
            return True
        
        except Exception as e:
            print(f"MP3 metadata error: {e}")
            return False
    
    async def _add_metadata_m4a(
        self, 
        filepath: Path, 
        metadata: Dict,
        cover_url: Optional[str]
    ) -> bool:
        """Добавление метаданных к M4A"""
        try:
            audio = MP4(str(filepath))
            
            if metadata.get('title'):
                audio.tags['\xa9nam'] = metadata['title']
            
            if metadata.get('artist'):
                audio.tags['\xa9ART'] = metadata['artist']
            
            if metadata.get('album'):
                audio.tags['\xa9alb'] = metadata['album']
            
            if metadata.get('release_date'):
                audio.tags['\xa9day'] = metadata['release_date']
            
            # Добавление обложки
            if cover_url:
                cover_data = await self._download_cover(cover_url)
                if cover_data:
                    audio.tags['covr'] = [
                        MP4Cover(cover_data, imageformat=MP4Cover.FORMAT_JPEG)
                    ]
            
            audio.save()
            return True
        
        except Exception as e:
            print(f"M4A metadata error: {e}")
            return False
    
    async def _download_cover(self, url: str) -> Optional[bytes]:
        """Загрузка обложки альбома"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as response:
                    if response.status == 200:
                        return await response.read()
            return None
        
        except Exception as e:
            print(f"Cover download error: {e}")
            return None
    
    async def convert_to_format(
        self, 
        input_file: Path, 
        output_format: str = 'mp3',
        bitrate: str = AUDIO_BITRATE
    ) -> Optional[Path]:
        """Конвертация аудио в указанный формат"""
        try:
            output_file = input_file.with_suffix(f'.{output_format}')
            
            cmd = [
                'ffmpeg',
                '-i', str(input_file),
                '-b:a', bitrate,
                '-vn',  # Без видео
                str(output_file),
                '-y'  # Перезапись
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            await process.communicate()
            
            if output_file.exists():
                return output_file
            
            return None
        
        except Exception as e:
            print(f"Conversion error: {e}")
            return None
    
    async def extract_audio_from_video(
        self, 
        video_file: Path,
        output_format: str = 'mp3'
    ) -> Optional[Path]:
        """Извлечение аудио из видео"""
        try:
            output_file = video_file.with_suffix(f'.{output_format}')
            
            cmd = [
                'ffmpeg',
                '-i', str(video_file),
                '-vn',  # Только аудио
                '-acodec', 'libmp3lame' if output_format == 'mp3' else 'copy',
                '-b:a', AUDIO_BITRATE,
                str(output_file),
                '-y'
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            await process.communicate()
            
            if output_file.exists():
                return output_file
            
            return None
        
        except Exception as e:
            print(f"Audio extraction error: {e}")
            return None
    
    def get_audio_duration(self, filepath: Path) -> Optional[int]:
        """Получение длительности аудио в секундах"""
        try:
            ext = filepath.suffix.lower()
            
            if ext == '.mp3':
                audio = MP3(str(filepath))
                return int(audio.info.length)
            elif ext == '.m4a':
                audio = MP4(str(filepath))
                return int(audio.info.length)
            
            return None
        
        except Exception:
            return None
