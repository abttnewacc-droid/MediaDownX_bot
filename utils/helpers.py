import re
import asyncio
from pathlib import Path
from typing import Optional, Iterable


def format_duration(seconds: int) -> str:
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    return f"{hours}:{minutes:02d}:{secs:02d}" if hours else f"{minutes}:{secs:02d}"


def format_filesize(bytes_size: int) -> str:
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if bytes_size < 1024:
            return f"{bytes_size:.1f} {unit}"
        bytes_size /= 1024
    return f"{bytes_size:.1f} PB"


def clean_filename(filename: str, max_length: int = 200) -> str:
    filename = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "", filename)
    filename = re.sub(r"\s+", " ", filename).strip()

    if len(filename) > max_length:
        if "." in filename:
            name, ext = filename.rsplit(".", 1)
            name = name[: max_length - len(ext) - 1]
            filename = f"{name}.{ext}"
        else:
            filename = filename[:max_length]

    return filename


def extract_urls_from_text(text: str) -> list[str]:
    url_pattern = (
        r"https?://[^\s<>\"']+"
    )
    return re.findall(url_pattern, text)


async def run_command(cmd: Iterable[str], timeout: int = 30) -> tuple[bool, str]:
    try:
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)
        output = (stdout or b"").decode(errors="ignore") + (stderr or b"").decode(errors="ignore")
        return process.returncode == 0, output

    except asyncio.TimeoutError:
        return False, "Command timeout"
    except Exception as e:
        return False, str(e)


async def safe_delete_file(filepath: Path, delay: int = 60):
    try:
        if delay > 0:
            await asyncio.sleep(delay)
        if filepath.exists():
            filepath.unlink(missing_ok=True)
    except Exception:
        pass
