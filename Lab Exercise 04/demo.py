"""Run the complete speech task demo from the terminal."""

from pathlib import Path
import Speech_task as st


def main() -> None:
    out_dir = Path("demo_output")
    out_dir.mkdir(exist_ok=True)

    sample_text = (
        "Hello, this is my local text to speech demonstration for the speech processing lab. "
        "In this first part, the program creates audio on the local machine and then uses that "
        "same generated sample as input for the local speech to text recognition stage."
    )
    sample_audio = out_dir / "local_demo.wav"
    dur = st.local_tts(sample_text, str(sample_audio))
    print(f"Local TTS: '{sample_text}' -> {sample_audio} ({dur:.2f}s)")

    recog = st.TemplateSpeechRecognizer(threshold=0.7)
    recog.add_template(sample_text, str(sample_audio))
    result = recog.recognise(str(sample_audio))
    print(f"Local STT: {result}")

    external_text = (
        "This is the external text to speech stage of my assignment. "
        "Here the system uses a free online speech service to generate audio, "
        "and then the resulting file is sent to the external speech to text system "
        "to verify that the transcription can be recovered automatically."
    )
    ext_audio = out_dir / "external_demo.mp3"
    ext_dur = st.external_tts(external_text, str(ext_audio))
    ext_audio_real = ext_audio if ext_audio.exists() and ext_audio.stat().st_size > 0 else ext_audio.with_suffix(".wav")
    print(f"External TTS: created {ext_audio_real} ({ext_dur:.2f}s)")

    transcript = st.external_stt(str(ext_audio_real))
    print(f"External STT: {transcript}")

    analysis = st.analyse_speech_signal(str(sample_audio))
    print(f"Extra speech task: {analysis}")

    print(f"Audio duration: {st.get_audio_duration(str(sample_audio)):.2f}s")


if __name__ == "__main__":
    main()
