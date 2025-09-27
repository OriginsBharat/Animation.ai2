import os
from moviepy.editor import (
    VideoFileClip,
    AudioFileClip,
    concatenate_videoclips,
    TextClip,
    CompositeVideoClip,
)
import moviepy.video.fx.all as vfx
import re

OUTPUT_PATH = "outputs"
os.makedirs(OUTPUT_PATH, exist_ok=True)

def parse_script_for_subtitles(script_text: str, audio_duration: float):
    """
    Parses a script and generates styled subtitle TextClips.
    This is a simplified parser. A real implementation would be more robust.
    """
    lines = [line.strip() for line in script_text.split('\n') if line.strip()]
    if not lines:
        return []

    num_lines = len(lines)
    duration_per_line = audio_duration / num_lines
    subtitles = []

    for i, line in enumerate(lines):
        start_time = i * duration_per_line

        # Remove emotional cues like (screaming) for the subtitle text
        clean_line = re.sub(r'\(.*?\)', '', line).strip()

        # Basic styling
        fontsize = 40
        font = "Arial-Bold"
        color = "white"
        stroke_color = "black"
        stroke_width = 2

        # Add emphasis for ALL CAPS text
        if clean_line.isupper() and len(clean_line) > 1:
            fontsize = 48

        txt_clip = (
            TextClip(
                clean_line,
                fontsize=fontsize,
                color=color,
                font=font,
                stroke_color=stroke_color,
                stroke_width=stroke_width,
                method="caption",
                size=(1080, 200), # Subtitle area width, height
            )
            .set_position(("center", "bottom"))
            .set_duration(duration_per_line)
            .set_start(start_time)
        )
        subtitles.append(txt_clip)

    return subtitles

def assemble_video(
    clip_paths: list[str],
    final_audio_path: str,
    script_text: str,
    output_filename: str = "final_video.mp4",
):
    """
    Stitches video clips together, adds the final audio, and overlays subtitles.
    """
    if not clip_paths or not final_audio_path:
        print("Error: Missing video clips or audio file.")
        return None

    try:
        print("--- Starting Video Assembly ---")

        # Load the final audio to get its duration
        final_audio = AudioFileClip(final_audio_path)
        audio_duration = final_audio.duration

        # Load video clips
        video_clips = [VideoFileClip(path) for path in clip_paths]

        # Concatenate clips and match duration to audio
        concatenated_clips = concatenate_videoclips(video_clips, method="compose")

        if concatenated_clips.duration > audio_duration:
            # Trim the video to match the audio
            final_video = concatenated_clips.subclip(0, audio_duration)
        elif concatenated_clips.duration < audio_duration:
            # If video is shorter, loop the last clip to fill the remaining time
            duration_to_fill = audio_duration - concatenated_clips.duration
            looped_last_clip = video_clips[-1].fx(vfx.loop, duration=duration_to_fill)
            final_video = concatenate_videoclips([concatenated_clips, looped_last_clip])
        else:
            final_video = concatenated_clips


        # Set the final audio
        final_video = final_video.set_audio(final_audio)

        # Generate and add subtitles
        subtitles = parse_script_for_subtitles(script_text, audio_duration)

        # Combine video with subtitles
        final_composition = CompositeVideoClip([final_video] + subtitles)

        # Write the final video file
        output_path = os.path.join(OUTPUT_PATH, output_filename)
        final_composition.write_videofile(
            output_path,
            codec="libx264",
            audio_codec="aac",
            temp_audiofile="temp-audio.m4a",
            remove_temp=True,
            logger="bar", # Use a progress bar
        )

        # Close clips to release resources
        final_audio.close()
        for clip in video_clips:
            clip.close()

        print(f"--- Video Assembly Complete. Saved to: {output_path} ---")
        return output_path

    except Exception as e:
        print(f"An error occurred during video assembly: {e}")
        # Clean up in case of error
        if 'final_audio' in locals(): final_audio.close()
        if 'video_clips' in locals():
            for clip in video_clips:
                clip.close()
        return None

if __name__ == '__main__':
    # Example for testing. Requires placeholder files.
    print("Testing video assembly module...")
    # This requires clips in the 'clips' folder and audio in 'outputs'
    # e.g., clips/clip_1.mp4, outputs/final_audio.mp3

    # You would need to run the other modules first to generate these files.
    # This is just a structural example.

    # test_clips = ["clips/my_clip_1.mp4", "clips/my_clip_2.mp4"]
    # test_audio = "outputs/final_audio.mp3"
    # test_script = "This is the first line.\nTHIS IS THE SECOND LINE (shouting)."

    # final_video_path = assemble_video(test_clips, test_audio, test_script)
    # if final_video_path:
    #     print(f"Test successful. Final video at: {final_video_path}")
    # else:
    #     print("Test failed. Ensure clip and audio files exist.")
    pass