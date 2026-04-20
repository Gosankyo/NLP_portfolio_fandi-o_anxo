from __future__ import annotations

import os
import subprocess
import wave
from pathlib import Path
from typing import Dict, Optional, Tuple

import numpy as np


def beep_tts(text: str, output_file: str, sample_rate: int = 44100) -> float:
    """Generate a simple beep-based WAV from text."""
    unique_chars = sorted(set(char for char in text.lower() if char.isalpha()))
    freq_map: Dict[str, float] = {char: 300.0 + 50.0 * index for index, char in enumerate(unique_chars)}

    tone_duration = 0.25
    audio = np.array([], dtype=np.float32)
    for char in text.lower():
        t = np.linspace(0, tone_duration, int(sample_rate * tone_duration), endpoint=False)
        if char.isalpha() and char in freq_map:
            tone = 0.5 * np.sin(2.0 * np.pi * freq_map[char] * t)
        else:
            tone = np.zeros_like(t)
        audio = np.concatenate((audio, tone))

    if np.max(np.abs(audio)) > 0:
        audio_int16 = (audio / np.max(np.abs(audio)) * 32767).astype(np.int16)
    else:
        audio_int16 = np.int16(audio)

    out_path = Path(output_file)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(out_path), "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(audio_int16.tobytes())

    return len(audio_int16) / sample_rate


def local_tts(text: str, output_file: str, rate: int = 165) -> float:
    """Run local text-to-speech on Windows, with beep fallback."""
    out_path = Path(output_file)
    if out_path.suffix.lower() != ".wav":
        out_path = out_path.with_suffix(".wav")
    out_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        escaped_path = str(out_path).replace("'", "''")
        escaped_text = text.replace("'", "''")
        ps_rate = max(-10, min(10, int(round((rate - 165) / 12))))
        command = (
            "Add-Type -AssemblyName System.Speech; "
            "$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
            f"$synth.Rate = {ps_rate}; "
            f"$synth.SetOutputToWaveFile('{escaped_path}'); "
            f"$synth.Speak('{escaped_text}'); "
            "$synth.Dispose();"
        )
        subprocess.run(
            ["powershell", "-NoProfile", "-Command", command],
            check=True,
            capture_output=True,
            text=True,
        )
        if out_path.exists() and out_path.stat().st_size > 0:
            return get_audio_duration(str(out_path))
        raise RuntimeError("Windows speech synthesizer did not create the audio file.")
    except Exception:
        return beep_tts(text, str(out_path))


class TemplateSpeechRecognizer:
    """Very small local STT system based on template matching."""

    def __init__(self, threshold: float = 0.8) -> None:
        self.templates: Dict[str, Tuple[int, np.ndarray]] = {}
        self.threshold = threshold

    def add_template(self, label: str, audio_path: str) -> None:
        with wave.open(audio_path, "rb") as wav_file:
            sample_rate = wav_file.getframerate()
            frames = wav_file.readframes(wav_file.getnframes())
            audio = np.frombuffer(frames, dtype=np.int16)
        self.templates[label] = (sample_rate, audio)

    def _similarity(self, first: np.ndarray, second: np.ndarray) -> float:
        length = min(len(first), len(second))
        if length == 0:
            return 0.0
        diff = np.mean(np.abs(first[:length].astype(np.float32) - second[:length].astype(np.float32))) / 32767.0
        return 1.0 - diff

    def recognise(self, audio_path: str) -> Optional[str]:
        with wave.open(audio_path, "rb") as wav_file:
            data = np.frombuffer(wav_file.readframes(wav_file.getnframes()), dtype=np.int16)

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


def external_tts(text: str, output_file: str, voice: str = "alloy") -> float:
    """Use a free external TTS API when available, otherwise fall back locally."""
    out_path = Path(output_file)
    if out_path.suffix.lower() not in {".mp3", ".wav"}:
        out_path = out_path.with_suffix(".mp3")
    out_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        from gtts import gTTS  # type: ignore

        tts = gTTS(text=text, lang="en", slow=False)
        tts.save(str(out_path))
        return get_audio_duration(str(out_path))
    except Exception:
        if out_path.exists() and out_path.stat().st_size == 0:
            out_path.unlink()

    return local_tts(text, str(out_path.with_suffix(".wav")))


def convert_audio_to_wav(audio_path: str, output_file: Optional[str] = None) -> str:
    """Convert MP3 or WAV audio into a WAV file for downstream processing."""
    source_path = Path(audio_path)
    if source_path.suffix.lower() == ".wav":
        return str(source_path)

    target_path = Path(output_file) if output_file else source_path.with_suffix(".wav")
    target_path.parent.mkdir(parents=True, exist_ok=True)

    import soundfile as sf  # type: ignore

    data, sample_rate = sf.read(str(source_path))
    sf.write(str(target_path), data, sample_rate)
    return str(target_path)


def external_stt(audio_path: str, language: str = "en") -> str:
    """Use a free external STT API through SpeechRecognition's Google backend."""
    try:
        import speech_recognition as sr  # type: ignore

        recognizer = sr.Recognizer()
        wav_path = convert_audio_to_wav(audio_path)
        with sr.AudioFile(wav_path) as source:
            audio_data = recognizer.record(source)
        return recognizer.recognize_google(audio_data, language=language).strip()
    except Exception:
        return "(external STT unavailable in this environment)"


def analyse_speech_signal(audio_path: str) -> Dict[str, float | str]:
    """Return a lightweight local speech-analysis summary beyond STT/TTS."""
    with wave.open(audio_path, "rb") as wav_file:
        sample_rate = wav_file.getframerate()
        audio = np.frombuffer(wav_file.readframes(wav_file.getnframes()), dtype=np.int16).astype(np.float32)

    if len(audio) == 0:
        return {
            "duration_seconds": 0.0,
            "rms_energy": 0.0,
            "zero_crossing_rate": 0.0,
            "activity_ratio": 0.0,
            "style": "silent",
        }

    normalised = audio / 32767.0
    duration_seconds = len(normalised) / float(sample_rate)
    rms_energy = float(np.sqrt(np.mean(np.square(normalised))))
    zero_crossings = np.abs(np.diff(np.signbit(normalised))).sum()
    zero_crossing_rate = float(zero_crossings / max(len(normalised) - 1, 1))
    activity_ratio = float(np.mean(np.abs(normalised) > 0.02))

    if activity_ratio < 0.15:
        style = "pause-heavy"
    elif rms_energy > 0.25:
        style = "energetic"
    else:
        style = "steady"

    return {
        "duration_seconds": round(duration_seconds, 2),
        "rms_energy": round(rms_energy, 4),
        "zero_crossing_rate": round(zero_crossing_rate, 4),
        "activity_ratio": round(activity_ratio, 4),
        "style": style,
    }


def get_audio_duration(audio_path: str) -> float:
    audio_suffix = Path(audio_path).suffix.lower()
    if audio_suffix == ".mp3":
        from mutagen.mp3 import MP3  # type: ignore

        return float(MP3(audio_path).info.length)

    with wave.open(audio_path, "rb") as wav_file:
        return wav_file.getnframes() / float(wav_file.getframerate())
