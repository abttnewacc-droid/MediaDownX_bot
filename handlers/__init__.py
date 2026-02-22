from .start import register as start_register
from .media import register as media_register
from .audio import register as audio_register
from .recognition import register as recognition_register

__all__ = [
    "start_register",
    "media_register",
    "audio_register",
    "recognition_register",
]
