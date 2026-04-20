"""
demo.py

This script demonstrates the functions in speech_tasks module.
It shows text-to-speech, speech recognition, and video creation.
Outputs are saved in a 'demo_output' directory.
"""

from pathlib import Path
import speech_tasks as st


def main() -> None:
    out_dir = Path("demo_output")
    out_dir.mkdir(exist_ok=True)
    
    # Generate audio
    sample_text = "hello world"
    sample_audio = out_dir / "hello_world.wav"
    dur = st.beep_tts(sample_text, str(sample_audio))
    print(f"Synthesized '{sample_text}' to {sample_audio} (duration: {dur:.2f}s)")
    
    # Recognize speech
    recog = st.TemplateSpeechRecognizer(threshold=0.7)
    recog.add_template(sample_text, str(sample_audio))
    result = recog.recognise(str(sample_audio))
    print(f"Recognition result: {result}")