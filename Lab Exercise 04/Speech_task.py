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
class TemplateSpeechRecognizer:
    """Template-based speech recogniser."""

    def __init__(self, threshold: float = 0.8) -> None:
        self.templates: Dict[str, Tuple[int, np.ndarray]] = {}
        self.threshold = threshold

    def add_template(self, label: str, audio_path: str) -> None:
        """Load a WAV file as a template."""
        with wave.open(audio_path, 'rb') as wf:
            sample_rate = wf.getframerate()
            frames = wf.readframes(wf.getnframes())
            audio = np.frombuffer(frames, dtype=np.int16)
        self.templates[label] = (sample_rate, audio)

    def _similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        length = min(len(a), len(b))
        if length == 0:
            return 0.0
        diff = np.mean(np.abs(a[:length].astype(np.float32) - b[:length].astype(np.float32))) / 32767.0
        return 1.0 - diff

    def recognise(self, audio_path: str) -> Optional[str]:
        """Return the best matching label."""
        with wave.open(audio_path, 'rb') as wf:
            data = np.frombuffer(wf.readframes(wf.getnframes()), dtype=np.int16)

        best_label = None
        best_score = -1.0
        for label, (_, template_data) in self.templates.items():
            score = self._similarity(data, template_data)
            if score > best_score:
                best_score = score
                best_label = label

        if best_score >= self.threshold:
            return best_label
        return None


def external_tts(text: str, output_file: str, voice: str = "en-US-JennyNeural") -> float:
    """Wrapper for remote TTS with local fallback."""
    try:
        import requests  # type: ignore

        api_base = "https://freetts.org/api"
        response = requests.post(
            f"{api_base}/tts",
            headers={"Content-Type": "application/json"},
            json={"text": text, "voice": voice, "rate": "+0%", "pitch": "+0Hz"},
        )
        response.raise_for_status()
        file_id = response.json().get("file_id")
        if not file_id:
            raise RuntimeError("No file_id")
        audio_resp = requests.get(f"{api_base}/audio/{file_id}")
        audio_resp.raise_for_status()

        out_path = Path(output_file)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, 'wb') as f:
            f.write(audio_resp.content)

        return len(audio_resp.content) * 8 / (128 * 1000)
    except Exception:
        out = Path(output_file)
        if out.suffix.lower() != '.wav':
            out = out.with_suffix('.wav')
        return beep_tts(text, str(out))


def external_stt(audio_path: str, language: str = "en") -> str:
    """Placeholder for external speech-to-text."""
    return "(external STT unavailable)"


def get_audio_duration(audio_path: str) -> float:
    """Return WAV duration."""
    with wave.open(audio_path, 'rb') as wf:
        return wf.getnframes() / float(wf.getframerate())


def create_demo_video(output_dir: str) -> str:
    """Create a demo video from generated audio."""
    from moviepy import VideoFileClip, AudioFileClip, concatenate_videoclips  # type: ignore

    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    audio_assets = {
        "template": out_dir / "template_hello.wav",
        "test_input": out_dir / "test_hello.wav",
        "local_tts": out_dir / "local_tts.wav",
        "external_tts": out_dir / "external_tts.wav",
    }