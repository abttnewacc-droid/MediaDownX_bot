import asyncio
import time
from pathlib import Path
from config import TEMP_DIR


class TempFileCleaner:
    """Сервис автоматической очистки временных файлов"""

    def __init__(self, max_age_minutes: int = 30):
        self.temp_dir: Path = TEMP_DIR
        self.max_age_seconds = max_age_minutes * 60
        self._task: asyncio.Task | None = None
        self._stop_event = asyncio.Event()

    async def start_auto_cleanup(self):
        """Запуск фоновой задачи очистки"""
        if self._task and not self._task.done():
            return

        self._stop_event.clear()
        self._task = asyncio.create_task(self._run())

    async def _run(self):
        while not self._stop_event.is_set():
            await self.cleanup_old_files()
            try:
                await asyncio.wait_for(self._stop_event.wait(), timeout=300)
            except asyncio.TimeoutError:
                pass

    async def cleanup_old_files(self):
        """Очистка старых файлов"""
        try:
            current_time = time.time()

            for file_path in self.temp_dir.iterdir():
                if not file_path.is_file():
                    continue

                try:
                    age = current_time - file_path.stat().st_mtime
                    if age > self.max_age_seconds:
                        file_path.unlink(missing_ok=True)
                except Exception:
                    continue

        except Exception:
            pass

    async def delete_file(self, filepath: Path, delay: int = 0):
        """Удаление конкретного файла с задержкой"""
        try:
            if delay > 0:
                await asyncio.sleep(delay)
            filepath.unlink(missing_ok=True)
        except Exception:
            pass

    def stop(self):
        """Корректная остановка фоновой задачи"""
        self._stop_event.set()
        if self._task:
            self._task.cancel()
