import os
import torch
from TTS.api import TTS
from pydub import AudioSegment

# --- Configuration ---
OUTPUTS_PATH = "outputs"
os.makedirs(OUTPUTS_PATH, exist_ok=True)

# --- TTS Model Setup ---
# This is done once to avoid reloading the model every time.
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"TTS using device: {device}")
# Using a multilingual voice cloning model
tts_model_name = "tts_models/multilingual/multi-dataset/xtts_v2"
try:
    tts = TTS(tts_model_name).to(device)
except Exception as e:
    print(f"Failed to load TTS model: {e}")
    tts = None

def generate_speech(script_text: str, speaker_wav_path: str, output_filename: str = "narration.wav"):
    """
    Generates speech from text using a speaker's voice sample.

    Args:
        script_text (str): The text to be synthesized.
        speaker_wav_path (str): Path to the audio file of the speaker's voice.
        output_filename (str): The name of the output audio file.

    Returns:
        str: The path to the generated audio file, or None on failure.
    """
    if not tts:
        print("TTS model is not available. Cannot generate speech.")
        return None

    if not os.path.exists(speaker_wav_path):
        print(f"Speaker WAV file not found at: {speaker_wav_path}")
        return None

    output_path = os.path.join(OUTPUTS_PATH, output_filename)

    print(f"Generating speech for script: '{script_text[:50]}...'")
    try:
        # The xtts_v2 model requires a language parameter. We'll default to English.
        tts.tts_to_file(
            text=script_text,
            speaker_wav=speaker_wav_path,
            language="en", # This could be made a user option in the future
            file_path=output_path
        )
        print(f"Speech successfully generated at: {output_path}")
        return output_path
    except Exception as e:
        print(f"An error occurred during TTS generation: {e}")
        return None

def mix_audio_with_ducking(narration_path: str, music_path: str, output_filename: str = "final_audio.mp3", trim_start_ms=0, trim_end_ms=None, ducking_amount_db=10):
    """
    Mixes narration audio with background music, applying trimming and audio ducking.

    Args:
        narration_path (str): Path to the narration audio file.
        music_path (str): Path to the background music file.
        output_filename (str): The name of the final mixed audio file.
        trim_start_ms (int): Start time for trimming music in milliseconds.
        trim_end_ms (int): End time for trimming music in milliseconds.
        ducking_amount_db (int): How much to lower the music volume (in dB) during narration.

    Returns:
        str: The path to the final mixed audio file, or None on failure.
    """
    try:
        print("Starting audio mixdown...")
        narration = AudioSegment.from_file(narration_path)
        music = AudioSegment.from_file(music_path)

        # 1. Trim background music
        if trim_end_ms is None:
            trim_end_ms = len(music)
        trimmed_music = music[trim_start_ms:trim_end_ms]
        print(f"Music trimmed to {len(trimmed_music) / 1000:.2f} seconds.")

        # 2. Apply audio ducking
        # When narration is present, music volume is reduced.
        # We'll make the music as long as the narration if it's shorter.
        if len(trimmed_music) < len(narration):
            trimmed_music = trimmed_music * (len(narration) // len(trimmed_music) + 1)
        trimmed_music = trimmed_music[:len(narration)]

        # Reduce the volume of the music track
        ducked_music = trimmed_music - ducking_amount_db
        print(f"Applied {ducking_amount_db}dB of ducking to music.")

        # 3. Overlay narration on top of the ducked music
        final_audio = ducked_music.overlay(narration)

        # 4. Export the final audio
        output_path = os.path.join(OUTPUTS_PATH, output_filename)
        final_audio.export(output_path, format="mp3")

        print(f"Final mixed audio saved to: {output_path}")
        return output_path

    except Exception as e:
        print(f"An error occurred during audio mixing: {e}")
        return None

def create_final_audio(script_text, speaker_wav, music_path, trim_start=0, trim_end=None):
    """
    Orchestrates the full audio generation pipeline.
    """
    print("--- Starting Full Audio Pipeline ---")

    # Step 1: Generate narration from script
    narration_audio_path = generate_speech(script_text, speaker_wav)
    if not narration_audio_path:
        return None

    # Step 2: Mix narration with background music
    if music_path:
        final_audio_path = mix_audio_with_ducking(
            narration_path=narration_audio_path,
            music_path=music_path,
            trim_start_ms=int(trim_start * 1000),
            trim_end_ms=int(trim_end * 1000) if trim_end is not None else None
        )
    else:
        # If no music, the final audio is just the narration
        final_audio_path = narration_audio_path

    print("--- Full Audio Pipeline Complete ---")
    return final_audio_path

if __name__ == '__main__':
    # This is an example for testing the module directly.
    # It requires placeholder files to exist.
    print("Testing audio module...")

    # Create dummy files for testing if they don't exist
    if not os.path.exists("test_speaker.wav"):
        AudioSegment.silent(duration=1000).export("test_speaker.wav", format="wav")
    if not os.path.exists("test_music.mp3"):
        AudioSegment.silent(duration=5000).export("test_music.mp3", format="mp3")

    test_script = "Hello world, this is a test of the AI voice generation system."
    final_path = create_final_audio(
        script_text=test_script,
        speaker_wav="test_speaker.wav",
        music_path="test_music.mp3",
        trim_start=1,
        trim_end=4
    )

    if final_path:
        print(f"\nTest successful. Final audio at: {final_path}")
    else:
        print("\nTest failed.")