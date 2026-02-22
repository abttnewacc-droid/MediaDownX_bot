# services/audio_processor.py
import asyncio
import aiohttp
from pathlib import Path
from typing import Optional, Dict

from mutagen.mp3 import MP3
from mutagen.id3 import ID3, TIT2, TPE1, TALB, APIC, TDRC
from mutagen.mp4 import MP4, MP4Cover

from config import TEMP_DIR, AUDIO_BITRATE


class AudioProcessor:
    """Сервис обработки аудио файлов и метаданных (стабильный, без сюрпризов)"""

    def __init__(self):
        self.temp_dir = TEMP_DIR

    async def add_metadata(
        self,
        filepath: Path,
        metadata: Dict,
        cover_url: Optional[str] = None
    ) -> bool:
        try:
            ext = filepath.suffix.lower()

            if ext == ".mp3":
                return await self._add_metadata_mp3(filepath, metadata, cover_url)
            elif ext == ".m4a":
                return await self._add_metadata_m4a(filepath, metadata, cover_url)

            return False
        except Exception:
            return False

    async def _add_metadata_mp3(
        self,
        filepath: Path,
        metadata: Dict,
        cover_url: Optional[str]
    ) -> bool:
        try:
            try:
                audio = MP3(filepath, ID3=ID3)
                audio.add_tags()
            except Exception:
                audio = MP3(filepath)

            if metadata.get("title"):
                audio.tags.add(TIT2(encoding=3, text=metadata["title"]))

            if metadata.get("artist"):
                audio.tags.add(TPE1(encoding=3, text=metadata["artist"]))

            if metadata.get("album"):
                audio.tags.add(TALB(encoding=3, text=metadata["album"]))

            if metadata.get("release_date"):
                audio.tags.add(TDRC(encoding=3, text=metadata["release_date"]))

            if cover_url:
                cover = await self._download_cover(cover_url)
                if cover:
                    audio.tags.add(
                        APIC(
                            encoding=3,
                            mime="image/jpeg",
                            type=3,
                            desc="Cover",
                            data=cover,
                        )
                    )

            audio.save()
            return True
        except Exception:
            return False

    async def _add_metadata_m4a(
        self,
        filepath: Path,
        metadata: Dict,
        cover_url: Optional[str]
    ) -> bool:
        try:
            audio = MP4(filepath)

            if metadata.get("title"):
                audio.tags["©nam"] = metadata["title"]

            if metadata.get("artist"):
                audio.tags["©ART"] = metadata["artist"]

            if metadata.get("album"):
                audio.tags["©alb"] = metadata["album"]

            if metadata.get("release_date"):
                audio.tags["©day"] = metadata["release_date"]

            if cover_url:
                cover = await self._download_cover(cover_url)
                if cover:
                    audio.tags["covr"] = [
                        MP4Cover(cover, imageformat=MP4Cover.FORMAT_JPEG)
                    ]

            audio.save()
            return True
        except Exception:
            return False

    async def _download_cover(self, url: str) -> Optional[bytes]:
        try:
            timeout = aiohttp.ClientTimeout(total=15)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url) as resp:
                    if resp.status == 200:
                        return await resp.read()
            return None
        except Exception:
            return None

    async def convert_to_mp3(self, input_file: Path) -> Optional[Path]:
        output = input_file.with_suffix(".mp3")

        cmd = [
            "ffmpeg",
            "-y",
            "-i", str(input_file),
            "-vn",
            "-ab", AUDIO_BITRATE,
            str(output),
        ]

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
        )
        await proc.communicate()

        return output if output.exists() else None

    async def extract_audio_from_video(self, video_file: Path) -> Optional[Path]:
        output = video_file.with_suffix(".mp3")

        cmd = [
            "ffmpeg",
            "-y",
            "-i", str(video_file),
            "-vn",
            "-ab", AUDIO_BITRATE,
            str(output),
        ]

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
        )
        await proc.communicate()

        return output if output.exists() else None

    def get_audio_duration(self, filepath: Path) -> Optional[int]:
        try:
            if filepath.suffix.lower() == ".mp3":
                return int(MP3(filepath).info.length)
            if filepath.suffix.lower() == ".m4a":
                return int(MP4(filepath).info.length)
            return None
        except Exception:
            return None
