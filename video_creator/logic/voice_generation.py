import os
from TTS.api import TTS

def generate_voice_audio(script: str, voice_sample_path: str, output_dir: str = "video_creator/temp") -> str:
    """
    Generates audio from a script using a cloned voice from a sample file.

    Args:
        script: The text script to be converted to speech.
        voice_sample_path: The path to the audio file to be used for voice cloning.
        output_dir: The directory to save the generated audio file.

    Returns:
        The path to the generated audio file, or None if generation fails.
    """
    try:
        print("Initializing TTS engine for voice cloning...")
        # Initialize the TTS engine with a multi-speaker, multi-lingual model that supports voice cloning
        tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2")

        # Ensure the output directory exists
        os.makedirs(output_dir, exist_ok=True)

        output_filename = "generated_voice.wav"
        output_path = os.path.join(output_dir, output_filename)

        print(f"Starting voice generation for script: '{script[:50]}...'")
        # Generate speech by cloning the voice from the provided audio file
        tts.tts_to_file(
            text=script,
            file_path=output_path,
            speaker_wav=voice_sample_path,
            language="en"  # Assuming English for now, can be parameterized later
        )

        print(f"Successfully generated voice audio at: {output_path}")
        return output_path

    except Exception as e:
        print(f"An error occurred during voice generation: {e}")
        # This can happen if the model needs to be downloaded for the first time
        # or if there's an issue with the input files.
        return None

if __name__ == '__main__':
    # This is a test block. To run this, you need a sample audio file.
    # Create a dummy voice sample for testing purposes.
    # In a real scenario, the user provides this.

    # Since we can't provide a real audio file here, we will just sketch out the test.
    # To test this manually:
    # 1. Place a short .wav file named 'sample.wav' in the root directory.
    # 2. Run this script: python3 video_creator/logic/voice_generation.py

    print("Running voice generation test...")

    # Create a dummy script
    test_script = "Hello, this is a test of the voice cloning system. I hope it sounds good."

    # Path to a hypothetical voice sample
    # IMPORTANT: This file must exist for the test to work.
    test_voice_sample = "sample.wav"

    if not os.path.exists(test_voice_sample):
        print("\nWARNING: Test cannot run without a 'sample.wav' file in the root directory.")
        print("Please add a short .wav audio file named 'sample.wav' to run the test.")
    else:
        generated_file = generate_voice_audio(test_script, test_voice_sample)
        if generated_file:
            print(f"\nTest successful! Audio file created at: {generated_file}")
        else:
            print("\nTest failed. Please check the error messages above.")