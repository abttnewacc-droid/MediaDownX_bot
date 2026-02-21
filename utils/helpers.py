import re
import asyncio
from typing import Optional
from pathlib import Path


def format_duration(seconds: int) -> str:
    """Форматирование длительности в читаемый вид"""
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    
    if hours > 0:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes}:{secs:02d}"


def format_filesize(bytes_size: int) -> str:
    """Форматирование размера файла"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.1f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.1f} TB"


def clean_filename(filename: str, max_length: int = 200) -> str:
    """Очистка имени файла от недопустимых символов"""
    # Удаление недопустимых символов
    filename = re.sub(r'[<>:"/\\|?*]', '', filename)
    
    # Замена множественных пробелов
    filename = re.sub(r'\s+', ' ', filename).strip()
    
    # Ограничение длины
    if len(filename) > max_length:
        name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
        name = name[:max_length - len(ext) - 1]
        filename = f"{name}.{ext}" if ext else name
    
    return filename


async def run_command(cmd: list, timeout: int = 30) -> tuple[bool, str]:
    """Выполнение shell команды с таймаутом"""
    try:
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await asyncio.wait_for(
            process.communicate(),
            timeout=timeout
        )
        
        return process.returncode == 0, stdout.decode() + stderr.decode()
    
    except asyncio.TimeoutError:
        return False, "Command timeout"
    except Exception as e:
        return False, str(e)


def extract_urls_from_text(text: str) -> list[str]:
    """Извлечение всех URL из текста"""
    url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    return re.findall(url_pattern, text)


async def safe_delete_file(filepath: Path, delay: int = 60):
    """Безопасное удаление файла с задержкой"""
    try:
        await asyncio.sleep(delay)
        if filepath.exists():
            filepath.unlink()
    except Exception:
        pass
