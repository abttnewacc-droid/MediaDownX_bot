import asyncio
import logging
from pathlib import Path
from typing import Optional, Dict, List

import yt_dlp

from config import TEMP_DIR, YT_DLP_OPTIONS, MAX_FILE_SIZE, DOWNLOAD_TIMEOUT

logger = logging.getLogger(__name__)


class MediaDownloader:
    """Сервис загрузки медиа через yt-dlp (унифицирован, без гонок и таймаутных крашей)"""

    def __init__(self):
        self.temp_dir = TEMP_DIR

    # ───────────────── INFO ─────────────────

    async def get_video_info(self, url: str) -> Optional[Dict]:
        try:
            ydl_opts = {
                **YT_DLP_OPTIONS,
                "skip_download": True,
                "noplaylist": True,
            }

            loop = asyncio.get_running_loop()
            return await asyncio.wait_for(
                loop.run_in_executor(
                    None, lambda: self._extract_info(url, ydl_opts)
                ),
                timeout=DOWNLOAD_TIMEOUT,
            )
        except Exception as e:
            logger.error(f"get_video_info failed: {e}")
            return None

    def _extract_info(self, url: str, opts: dict) -> Dict:
        with yt_dlp.YoutubeDL(opts) as ydl:
            return ydl.extract_info(url, download=False)

    # ───────────────── QUALITIES ─────────────────

    async def get_available_qualities(self, url: str) -> List[Dict]:
        info = await self.get_video_info(url)
        if not info:
            return []

        formats = info.get("formats", [])
        qualities = []
        seen = set()

        for f in formats:
            height = f.get("height")
            if not height or height in seen:
                continue
            if f.get("vcodec") == "none":
                continue

            qualities.append(
                {
                    "height": height,
                    "format_id": f.get("format_id"),
                    "ext": f.get("ext", "mp4"),
                    "filesize": f.get("filesize") or 0,
                    "fps": f.get("fps") or 30,
                }
            )
            seen.add(height)

        return sorted(qualities, key=lambda x: x["height"])

    # ───────────────── DOWNLOAD ─────────────────

    async def download_video(
        self,
        url: str,
        quality: str = "best",
        audio_only: bool = False,
        progress_callback=None,
    ) -> Optional[Path]:
        filename = self.temp_dir / self._generate_filename()

        if audio_only:
            ydl_opts = {
                **YT_DLP_OPTIONS,
                "format": "bestaudio/best",
                "outtmpl": str(filename),
                "postprocessors": [
                    {
                        "key": "FFmpegExtractAudio",
                        "preferredcodec": "mp3",
                        "preferredquality": "320",
                    }
                ],
            }
        else:
            if quality == "best":
                fmt = "bv*+ba/best"
            else:
                fmt = f"bv*[height<={quality}]+ba/best"

            ydl_opts = {
                **YT_DLP_OPTIONS,
                "format": fmt,
                "outtmpl": str(filename),
                "merge_output_format": "mp4",
            }

        if progress_callback:
            ydl_opts["progress_hooks"] = [
                lambda d: asyncio.create_task(progress_callback(d))
            ]

        try:
            loop = asyncio.get_running_loop()
            await asyncio.wait_for(
                loop.run_in_executor(None, lambda: self._download(url, ydl_opts)),
                timeout=DOWNLOAD_TIMEOUT,
            )
            return self._find_downloaded_file(filename)
        except Exception as e:
            logger.error(f"download_video failed: {e}")
            return None

    def _download(self, url: str, opts: dict):
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([url])

    # ───────────────── FILE FIND ─────────────────

    def _find_downloaded_file(self, base: Path) -> Optional[Path]:
        if base.exists():
            return base

        for ext in [".mp4", ".webm", ".mkv", ".mp3", ".m4a"]:
            p = base.with_suffix(ext)
            if p.exists():
                return p

        for f in base.parent.glob(base.stem + "*"):
            if f.is_file():
                return f

        return None

    # ───────────────── IMAGE ─────────────────

    async def download_image(self, url: str) -> Optional[Path]:
        filename = self.temp_dir / f"{self._generate_filename()}.jpg"
        ydl_opts = {
            **YT_DLP_OPTIONS,
            "outtmpl": str(filename),
            "skip_download": False,
        }

        try:
            loop = asyncio.get_running_loop()
            await asyncio.wait_for(
                loop.run_in_executor(None, lambda: self._download(url, ydl_opts)),
                timeout=DOWNLOAD_TIMEOUT,
            )
            return self._find_downloaded_file(filename)
        except Exception as e:
            logger.error(f"download_image failed: {e}")
            return None

    # ───────────────── DIRECT ─────────────────

    async def download_direct_url(self, url: str) -> Optional[Path]:
        import aiohttp
        import aiofiles

        filename = self.temp_dir / self._generate_filename()

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=30) as resp:
                    if resp.status != 200:
                        return None

                    ct = resp.headers.get("Content-Type", "")
                    ext = self._get_extension_from_content_type(ct)
                    if not ext:
                        ext = Path(url).suffix or ".bin"

                    path = filename.with_suffix(ext)
                    async with aiofiles.open(path, "wb") as f:
                        await f.write(await resp.read())
                    return path
        except Exception as e:
            logger.error(f"download_direct_url failed: {e}")
            return None

    # ───────────────── HELPERS ─────────────────

    def _get_extension_from_content_type(self, ct: str) -> str:
        return {
            "video/mp4": ".mp4",
            "video/webm": ".webm",
            "image/jpeg": ".jpg",
            "image/png": ".png",
            "image/gif": ".gif",
            "audio/mpeg": ".mp3",
            "audio/mp4": ".m4a",
        }.get(ct, "")

    def _generate_filename(self) -> str:
        import time, random

        return f"media_{int(time.time() * 1000)}_{random.randint(1000,9999)}"

    async def get_thumbnail(self, url: str) -> Optional[str]:
        info = await self.get_video_info(url)
        return info.get("thumbnail") if info else None
