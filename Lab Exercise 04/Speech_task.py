# Libraries
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional, Tuple

import numpy as np
import wave
import cv2 

def beep_tts(text: str, output_file: str, sample_rate: int = 44100) -> float:
    """Generate a beep WAV from text."""
    unique_chars = sorted(set(c for c in text.lower() if c.isalpha()))
    freq_map: Dict[str, float] = {char: 300.0 + 50.0 * i for i, char in enumerate(unique_chars)}

    tone_duration = 0.25
    audio = np.array([], dtype=np.float32)
    for char in text.lower():
        t = np.linspace(0, tone_duration, int(sample_rate * tone_duration), endpoint=False)
        if char.isalpha() and char in freq_map:
            freq = freq_map[char]
            tone = 0.5 * np.sin(2.0 * np.pi * freq * t)
        else:
            tone = np.zeros_like(t)
        audio = np.concatenate((audio, tone))

# normalise to int16 range
    if np.max(np.abs(audio)) > 0:
        audio_int16 = (audio / np.max(np.abs(audio)) * 32767).astype(np.int16)
    else:
        audio_int16 = np.int16(audio)

    out_path = Path(output_file)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(out_path), 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(audio_int16.tobytes())

    return len(audio_int16) / sample_rate