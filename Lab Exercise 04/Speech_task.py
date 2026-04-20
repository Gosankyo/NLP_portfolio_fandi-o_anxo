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
     # create audio files for the demo
    beep_tts("hello world", str(audio_assets["template"]))
    beep_tts("hello world", str(audio_assets["test_input"]))
    beep_tts("this is local t t s", str(audio_assets["local_tts"]))
    external_tts("this is external t t s", str(audio_assets["external_tts"]))

    recogniser = TemplateSpeechRecognizer(threshold=0.7)
    recogniser.add_template("hello world", str(audio_assets["template"]))
    recog = recogniser.recognise(str(audio_assets["test_input"])) or "unrecognised"
    ext_transcript = external_stt(str(audio_assets["test_input"]))

    durations = {k: get_audio_duration(str(v)) for k, v in audio_assets.items()}

    def make_slide(text: str, duration: float, filename: str) -> Path:
        width, height = 640, 480
        fps = 24
        total_frames = int(round(duration * fps)) or 1
        frame = np.zeros((height, width, 3), dtype=np.uint8)

        lines: list[str] = []
        words = text.split()
        line = ""
        for word in words:
            if len(line) + len(word) + 1 > 35:
                lines.append(line)
                line = word
            else:
                line = f"{line} {word}".strip()
        if line:
            lines.append(line)

        y_offset = 200 - 20 * (len(lines) - 1)
        for i, l in enumerate(lines):
            cv2.putText(
                frame,
                l,
                (40, y_offset + i * 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (255, 255, 255),
                2,
                cv2.LINE_AA,
            )

        temp_video_path = out_dir / filename
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        writer = cv2.VideoWriter(str(temp_video_path), fourcc, fps, (width, height))
        for _ in range(total_frames):
            writer.write(frame)
        writer.release()
        return temp_video_path

    slides: list[tuple[Path, str, float]] = []
    slides.append((make_slide("Intro: local TTS and STT demo.", durations["local_tts"], "intro.mp4"), str(audio_assets["local_tts"]), durations["local_tts"]))
    slides.append((make_slide("Local TTS: generated beeps.", durations["local_tts"], "local_tts.mp4"), str(audio_assets["local_tts"]), durations["local_tts"]))
    slides.append((make_slide("External TTS: remote API fallback.", durations["external_tts"], "external_tts.mp4"), str(audio_assets["external_tts"]), durations["external_tts"]))
    slides.append((make_slide(f"Local STT result: '{recog}'.", durations["test_input"], "local_stt.mp4"), str(audio_assets["test_input"]), durations["test_input"]))
    slides.append((make_slide(f"External STT result: {ext_transcript}", 4.0, "external_stt.mp4"), str(audio_assets["template"]), 4.0))
    slides.append((make_slide(f"Duration: {durations['template']:.2f} sec.", durations["template"], "duration.mp4"), str(audio_assets["template"]), durations["template"]))

    clips = []
    for vid_path, aud_path, _ in slides:
        clip = VideoFileClip(str(vid_path)).with_audio(AudioFileClip(aud_path))
        clips.append(clip)

    final_clip = concatenate_videoclips(clips, method="compose")
    out_video_path = out_dir / "speech_demo.mp4"
    final_clip.write_videofile(str(out_video_path), fps=24)
    for clip in clips:
        clip.close()
    final_clip.close()
    return str(out_video_path)