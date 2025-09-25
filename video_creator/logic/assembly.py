import re

def parse_script(script: str) -> list:
    """
    Parses a script with emotional cues into a structured list.

    Args:
        script: The input script, e.g., "Hello world (HAPPY). How are you? (NEUTRAL)"

    Returns:
        A list of tuples, where each tuple is (dialogue, emotion).
        e.g., [('Hello world', 'happy'), ('How are you?', 'neutral')]
    """
    structured_script = []
    last_index = 0

    # Find all emotion cues, e.g., (HAPPY)
    matches = list(re.finditer(r'\((.*?)\)', script))

    for match in matches:
        # The text before the current match
        start, end = match.span()
        dialogue = script[last_index:start].strip()
        emotion = match.group(1).strip().lower()

        if dialogue:
            structured_script.append((dialogue, emotion))

        last_index = end

    # Handle any remaining text after the last match
    remaining_text = script[last_index:].strip()
    if remaining_text:
        structured_script.append((remaining_text, "neutral"))

    return structured_script

def create_storyboard(parsed_script: list, analyzed_clips: list) -> list:
    """
    Creates a storyboard by matching script emotions to clip emotions.

    Args:
        parsed_script: The output from parse_script().
        analyzed_clips: A list of dicts, e.g., [{'path': '...', 'emotion': '...'}].

    Returns:
        A list of tuples, where each tuple is (dialogue, clip_path).
    """
    storyboard = []

    # Simple matching: for each dialogue segment, find a clip with the matching emotion.
    for dialogue, emotion in parsed_script:
        # Find all clips that match the required emotion
        matching_clips = [c for c in analyzed_clips if c['emotion'] == emotion]

        if matching_clips:
            # For now, just pick the first matching clip.
            # A more advanced version could use random.choice or other logic.
            storyboard.append((dialogue, matching_clips[0]['path']))
        else:
            # If no direct match, try to find a 'neutral' clip as a fallback
            neutral_clips = [c for c in analyzed_clips if c['emotion'] == 'neutral']
            if neutral_clips:
                storyboard.append((dialogue, neutral_clips[0]['path']))
            else:
                # If still no clip is found, we have to skip this dialogue segment
                print(f"Warning: No clip found for emotion '{emotion}' or neutral. Skipping dialogue: '{dialogue}'")

    return storyboard

def assemble_final_video(storyboard: list, voice_over_path: str, music_path: str, output_path: str = "final_video.mp4"):
    """
    Assembles the final video from the storyboard, audio, and music.

    Args:
        storyboard: The storyboard from create_storyboard().
        voice_over_path: Path to the generated voice-over audio file.
        music_path: Path to the background music file.
        output_path: The path to save the final video file.
    """
    # This function will be implemented in a subsequent step.
    # It will use moviepy to:
    # 1. Load each clip from the storyboard.
    # 2. Create a TextClip for the dialogue and overlay it on the video clip.
    # 3. Concatenate all the video clips together.
    # 4. Load the voice-over and background music.
    # 5. Set the final video's audio to be the composite of the voice-over and music.
    # 6. Write the final video to the output_path.
    try:
        from moviepy.editor import VideoFileClip, AudioFileClip, CompositeAudioClip, TextClip, CompositeVideoClip
        import moviepy.audio.fx.all as afx

        print("Starting final video assembly...")

        # Step 1: Generate video clips with text overlays
        final_clips = []
        current_time = 0
        for dialogue, clip_path in storyboard:
            video_clip = VideoFileClip(clip_path)

            # Create a text clip for the dialogue
            txt_clip = TextClip(dialogue, fontsize=40, color='white', font='Arial-Bold',
                                stroke_color='black', stroke_width=2)
            txt_clip = txt_clip.set_position('center').set_duration(video_clip.duration)

            # Overlay the text on the video clip
            video_with_text = CompositeVideoClip([video_clip, txt_clip])
            final_clips.append(video_with_text)
            current_time += video_clip.duration

        # Step 2: Concatenate all video clips
        final_video = CompositeVideoClip(final_clips)

        # Step 3: Prepare audio
        voice_over = AudioFileClip(voice_over_path)
        music = AudioFileClip(music_path)

        # Loop music if it's shorter than the video
        if music.duration < final_video.duration:
            music = music.fx(afx.audio_loop, duration=final_video.duration)

        # Lower music volume (audio ducking)
        music = music.volumex(0.2)

        # Combine voice-over and music
        final_audio = CompositeAudioClip([voice_over.set_start(0), music])
        final_audio.duration = final_video.duration

        # Step 4: Set the final audio and write the video file
        final_video = final_video.set_audio(final_audio)
        final_video.write_videofile(output_path, codec='libx264', audio_codec='aac', fps=24)

        print(f"Successfully assembled final video at: {output_path}")

    except Exception as e:
        print(f"An error occurred during final video assembly: {e}")


if __name__ == '__main__':
    # This test block will be expanded later to test the full assembly.
    pass