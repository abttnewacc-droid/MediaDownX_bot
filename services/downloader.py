# services/downloader.py
import asyncio
import yt_dlp
from pathlib import Path
from typing import Optional, Dict, List, Any
from config import TEMP_DIR, YT_DLP_OPTIONS, MAX_FILE_SIZE
from utils.helpers import clean_filename


class MediaDownloader:
    """Сервис загрузки медиа через yt-dlp (устойчивый к Shorts / Reels / playlists)."""

    def __init__(self):
        # гарантируем, что temp_dir это Path и директория существует
        self.temp_dir = Path(TEMP_DIR) if not isinstance(TEMP_DIR, Path) else TEMP_DIR
        self.temp_dir.mkdir(parents=True, exist_ok=True)

    async def get_video_info(self, url: str) -> Optional[Dict[str, Any]]:
        """Получение информации о видео. Если вернулся плейлист/entries — возвращаем первый элемент."""
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

            if not info:
                return None

            # yt-dlp иногда возвращает плейлист/медиа-контейнер с 'entries'
            if isinstance(info, dict) and 'entries' in info and info['entries']:
                # берем первый валидный элемент
                for entry in info['entries']:
                    if entry:
                        return entry
                return None

            return info

        except Exception as e:
            print(f"[downloader.get_video_info] Error getting video info for {url}: {e}")
            return None

    def _extract_info(self, url: str, opts: dict) -> Optional[dict]:
        """Синхронное извлечение информации через yt_dlp."""
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                return ydl.extract_info(url, download=False)
        except Exception as e:
            print(f"[downloader._extract_info] yt-dlp exception for {url}: {e}")
            return None

    async def get_available_qualities(self, url: str) -> List[Dict[str, Any]]:
        """Получение доступных качеств видео (список уникальных высот с минимальной информацией)."""
        info = await self.get_video_info(url)
        if not info:
            return []

        formats = info.get('formats') or []
        qualities: List[Dict[str, Any]] = []
        seen_heights = set()

        for fmt in formats:
            # защита: иногда height может быть None или float-like
            height = fmt.get('height')
            try:
                if height is None:
                    # попытка извлечь из format_note или format
                    note = fmt.get('format_note') or fmt.get('format')
                    if note and isinstance(note, str):
                        import re
                        m = re.search(r'(\d+)[pP]', note)
                        if m:
                            height = int(m.group(1))
                else:
                    height = int(height)
            except Exception:
                height = None

            if not height or height in seen_heights:
                continue

            # проверяем, что поток содержит видео (vcodec != 'none')
            vcodec = fmt.get('vcodec')
            if vcodec is None:
                # если нет явного vcodec, допускаем этот формат (бывают нестандартные записи)
                has_video = True
            else:
                has_video = (vcodec != 'none')

            if not has_video:
                continue

            # безопасный filesize (int или None)
            filesize = fmt.get('filesize') or fmt.get('filesize_approx') or 0
            try:
                if filesize is None:
                    filesize_int = 0
                else:
                    filesize_int = int(filesize)
            except Exception:
                filesize_int = 0

            qualities.append({
                'height': height,
                'format_id': fmt.get('format_id') or fmt.get('format'),
                'ext': fmt.get('ext') or 'mp4',
                'filesize': filesize_int,
                'fps': fmt.get('fps') or 0,
            })
            seen_heights.add(height)

        # сортировка по возрастанию (от низшего к высшему)
        qualities.sort(key=lambda x: x['height'])
        return qualities

    async def download_video(
        self,
        url: str,
        quality: str = 'best',
        audio_only: bool = False,
        progress_callback=None
    ) -> Optional[Path]:
        """Загрузка видео (или аудио) через yt-dlp. Возвращает путь к файлу или None."""
        try:
            # подготовка базового имени (без расширения)
            raw_name = self._generate_filename()
            filename_base = self.temp_dir / clean_filename(raw_name)

            # если audio_only — используем postprocessor
            if audio_only:
                ydl_opts = {
                    **YT_DLP_OPTIONS,
                    'format': 'bestaudio/best',
                    'outtmpl': str(filename_base) + '.%(ext)s',
                    'postprocessors': [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                        'preferredquality': '320',
                    }],
                }
            else:
                # качество может быть 'best' или числом/строкой '720'/'720p'
                if isinstance(quality, (int, float)):
                    q_val = int(quality)
                else:
                    # попытка извлечь цифры
                    import re
                    m = re.search(r'(\d+)', str(quality))
                    q_val = int(m.group(1)) if m else None

                if not q_val:
                    # best fallback
                    format_selector = 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'
                else:
                    # используем безопасную конструкцию: height<=q_val
                    format_selector = f'bestvideo[height<={q_val}][ext=mp4]+bestaudio[ext=m4a]/best[height<={q_val}][ext=mp4]/best'

                ydl_opts = {
                    **YT_DLP_OPTIONS,
                    'format': format_selector,
                    'outtmpl': str(filename_base) + '.%(ext)s',
                    'merge_output_format': 'mp4',
                }

            # progress hook - аккуратно: callback может быть async или sync
            if progress_callback:
                def _hook(d):
                    try:
                        # если progress_callback - coroutine function
                        result = progress_callback(d)
                        if asyncio.iscoroutine(result):
                            asyncio.get_event_loop().create_task(result)
                    except Exception as e:
                        # не даём падать из-за хука
                        print(f"[downloader.progress_hook] hook error: {e}")

                ydl_opts['progress_hooks'] = [_hook]

            loop = asyncio.get_event_loop()
            # запускаем загрузку в executor (blocking)
            await loop.run_in_executor(
                None,
                lambda: self._download(url, ydl_opts)
            )

            # Ищем скачанный файл
            downloaded_file = self._find_downloaded_file(str(filename_base))
            # проверяем размер MAX_FILE_SIZE если задан
            if downloaded_file and MAX_FILE_SIZE:
                try:
                    size = downloaded_file.stat().st_size
                    if MAX_FILE_SIZE > 0 and size > MAX_FILE_SIZE:
                        print(f"[downloader] Downloaded file too large: {size} > {MAX_FILE_SIZE}")
                        # удаляем файл и возвращаем None
                        try:
                            downloaded_file.unlink()
                        except Exception:
                            pass
                        return None
                except Exception:
                    pass

            return downloaded_file

        except Exception as e:
            print(f"[downloader.download_video] Download error for {url}: {e}")
            return None

    def _download(self, url: str, opts: dict):
        """Синхронная загрузка (внутри executor)."""
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                ydl.download([url])
        except Exception as e:
            # пробрасываем исключение вверх через print — run_in_executor поймает
            print(f"[downloader._download] yt-dlp download exception: {e}")
            raise

    def _find_downloaded_file(self, base_filename: str) -> Optional[Path]:
        """Поиск скачанного файла по outtmpl базе. Поддерживает разные расширения и окончательные имена."""
        base_path = Path(base_filename)

        # если файл с точным именем (без суффикса) существует — возвращаем
        if base_path.exists() and base_path.is_file():
            return base_path

        # ищем расширения, которые мог поставить yt-dlp (%(ext)s -> .mp4/.m4a/.webm/.mp3)
        possible_exts = ['.mp4', '.webm', '.mkv', '.mp3', '.m4a', '.mkv', '.ogg']
        for ext in possible_exts:
            p = base_path.with_suffix(ext)
            if p.exists():
                return p

        # если yt-dlp сгенерировал имя с title/other tokens, пробуем матч по шаблону
        parent_dir = base_path.parent
        stem_pattern = base_path.stem
        for file in parent_dir.glob(f"{stem_pattern}*"):
            if file.is_file():
                return file

        return None

    async def download_image(self, url: str) -> Optional[Path]:
        """Загрузка изображения через yt-dlp (устойчиво для Instagram/Pinterest)."""
        try:
            raw_name = self._generate_filename()
            filename = self.temp_dir / (clean_filename(raw_name) + '.%(ext)s')

            ydl_opts = {
                **YT_DLP_OPTIONS,
                'outtmpl': str(filename),
            }

            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: self._download(url, ydl_opts)
            )

            downloaded_file = self._find_downloaded_file(str(self.temp_dir / clean_filename(raw_name)))
            return downloaded_file
        except Exception as e:
            print(f"[downloader.download_image] Image download error for {url}: {e}")
            return None

    async def download_direct_url(self, url: str) -> Optional[Path]:
        """Загрузка по прямой ссылке (без yt-dlp)."""
        import aiohttp
        import aiofiles

        try:
            raw_name = self._generate_filename()
            filename = self.temp_dir / clean_filename(raw_name)

            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        # Определение расширения
                        content_type = response.headers.get('Content-Type', '')
                        ext = self._get_extension_from_content_type(content_type)

                        if not ext:
                            ext = Path(url).suffix or '.bin'

                        filepath = Path(f"{filename}{ext}")

                        async with aiofiles.open(filepath, 'wb') as f:
                            await f.write(await response.read())

                        return filepath

            return None

        except Exception as e:
            print(f"[downloader.download_direct_url] Direct download error for {url}: {e}")
            return None

    def _get_extension_from_content_type(self, content_type: str) -> str:
        mapping = {
            'video/mp4': '.mp4',
            'video/webm': '.webm',
            'image/jpeg': '.jpg',
            'image/png': '.png',
            'image/gif': '.gif',
            'audio/mpeg': '.mp3',
            'audio/mp4': '.m4a',
        }
        return mapping.get(content_type.split(';')[0].strip(), '')

    def _generate_filename(self) -> str:
        """Генерация уникального имени файла без расширения."""
        import time
        import random
        timestamp = int(time.time() * 1000)
        random_suffix = random.randint(1000, 9999)
        return f"media_{timestamp}_{random_suffix}"

    async def get_thumbnail(self, url: str) -> Optional[str]:
        """Получение URL превью видео (устойчиво к разным полям)."""
        info = await self.get_video_info(url)
        if not info:
            return None

        # первичный вариант
        thumb = info.get('thumbnail')
        if thumb:
            return thumb

        # иногда thumbnail - список в 'thumbnails'
        thumbs = info.get('thumbnails') or []
        if isinstance(thumbs, list) and thumbs:
            # берем самую крупную доступную
            try:
                thumbs_sorted = sorted(
                    (t for t in thumbs if isinstance(t, dict) and t.get('url')),
                    key=lambda x: int(x.get('width') or 0),
                    reverse=True
                )
                return thumbs_sorted[0].get('url')
            except Exception:
                return thumbs[0].get('url')

        return None
