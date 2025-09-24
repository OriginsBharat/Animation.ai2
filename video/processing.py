import numpy as np
from moviepy.editor import ImageSequenceClip, AudioFileClip, CompositeVideoClip, TextClip

def create_animation_video(image_sequence: list, output_path: str, fps: int, audio_path: str = None, text_overlays: list = None):
    """
    Creates a video from a sequence of images and adds audio and text.

    Args:
        image_sequence: A list of PIL Images or numpy arrays.
        output_path: The path to save the output MP4 file.
        fps: The frames per second for the video.
        audio_path: Optional path to an audio file to add to the video.
        text_overlays: Optional list of dictionaries for text overlays.
                       Each dict should be e.g., {'text': 'Hello', 'start': 1, 'duration': 2}
    """
    print(f"Beginning video creation process...")

    # Moviepy works with numpy arrays
    numpy_sequence = [np.array(img) for img in image_sequence]

    # Create the video clip from the image sequence
    video_clip = ImageSequenceClip(numpy_sequence, fps=fps)

    clips_to_composite = [video_clip]

    # Add audio if provided
    if audio_path:
        try:
            audio_clip = AudioFileClip(audio_path)
            # Set video duration to match audio duration if it's shorter
            if audio_clip.duration < video_clip.duration:
                video_clip = video_clip.set_duration(audio_clip.duration)
            video_clip.audio = audio_clip
        except Exception as e:
            print(f"Warning: Could not process audio file {audio_path}. Error: {e}")
            # Ensure video has some duration if audio fails
            if not video_clip.duration:
                video_clip = video_clip.set_duration(len(image_sequence) / fps)


    # Add text overlays if provided
    if text_overlays:
        for overlay in text_overlays:
            txt_clip = TextClip(overlay['text'], fontsize=70, color='white', font='Arial-Bold', stroke_color='black', stroke_width=2)
            txt_clip = txt_clip.set_pos('center').set_start(overlay['start']).set_duration(overlay['duration'])
            clips_to_composite.append(txt_clip)

    # Composite all clips together
    final_clip = CompositeVideoClip(clips_to_composite, size=video_clip.size)
    final_clip = final_clip.set_duration(video_clip.duration)


    # Write the final video file
    try:
        final_clip.write_videofile(output_path, codec='libx264', audio_codec='aac', fps=fps)
        print(f"Video successfully saved to {output_path}")
    except Exception as e:
        print(f"Error writing video file: {e}")
    finally:
        # It's good practice to close clips to free up resources
        if 'audio_clip' in locals():
            audio_clip.close()
        video_clip.close()
        final_clip.close()


if __name__ == '__main__':
    from PIL import Image
    print("Testing video processing module...")

    # Create a dummy sequence of images for testing
    img1 = Image.new('RGB', (640, 480), color = 'red')
    img2 = Image.new('RGB', (640, 480), color = 'green')
    img3 = Image.new('RGB', (640, 480), color = 'blue')
    test_sequence = [img1, img2, img3] * 10 # 30 frames total

    # Define text overlays
    test_overlays = [
        {'text': 'START', 'start': 0, 'duration': 0.5},
        {'text': 'END', 'start': 1.0, 'duration': 0.5}
    ]

    # Create a dummy output path
    output_file = "test_animation.mp4"

    print("Generating test video...")
    # We won't use audio here for simplicity, but the function supports it.
    create_animation_video(test_sequence, output_file, fps=24, text_overlays=test_overlays)

    # In a real run, you would check if "test_animation.mp4" was created.
    # To clean up, you might run: os.remove(output_file)
    print("Test finished. Check for 'test_animation.mp4' in the root directory.")
