import asyncio
import time
from pathlib import Path
from config import TEMP_DIR


class TempFileCleaner:
    """Сервис автоматической очистки временных файлов"""
    
    def __init__(self, max_age_minutes: int = 30):
        self.temp_dir = TEMP_DIR
        self.max_age_seconds = max_age_minutes * 60
        self.is_running = False
    
    async def start_auto_cleanup(self):
        """Запуск автоматической очистки"""
        self.is_running = True
        
        while self.is_running:
            await self.cleanup_old_files()
            await asyncio.sleep(300)  # Проверка каждые 5 минут
    
    async def cleanup_old_files(self):
        """Очистка старых файлов"""
        try:
            current_time = time.time()
            deleted_count = 0
            
            for file_path in self.temp_dir.iterdir():
                if file_path.is_file():
                    file_age = current_time - file_path.stat().st_mtime
                    
                    if file_age > self.max_age_seconds:
                        try:
                            file_path.unlink()
                            deleted_count += 1
                        except Exception as e:
                            print(f"Failed to delete {file_path}: {e}")
            
            if deleted_count > 0:
                print(f"Cleaned up {deleted_count} old files")
        
        except Exception as e:
            print(f"Cleanup error: {e}")
    
    async def delete_file(self, filepath: Path, delay: int = 0):
        """Удаление конкретного файла с задержкой"""
        try:
            if delay > 0:
                await asyncio.sleep(delay)
            
            if filepath.exists():
                filepath.unlink()
        
        except Exception as e:
            print(f"Delete error for {filepath}: {e}")
    
    def stop(self):
        """Остановка автоочистки"""
        self.is_running = False
