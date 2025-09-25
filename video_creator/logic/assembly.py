import re
from moviepy.editor import VideoFileClip, AudioFileClip, CompositeAudioClip, TextClip, CompositeVideoClip
import moviepy.audio.fx.all as afx

def parse_script(script: str) -> list:
    """
    Parses a script with emotional cues into a structured list.
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
    """
    storyboard = []

    for dialogue, emotion in parsed_script:
        matching_clips = [c for c in analyzed_clips if c['emotion'] == emotion]

        if matching_clips:
            storyboard.append((dialogue, matching_clips[0]['path']))
        else:
            neutral_clips = [c for c in analyzed_clips if c['emotion'] == 'neutral']
            if neutral_clips:
                storyboard.append((dialogue, neutral_clips[0]['path']))
            else:
                print(f"Warning: No clip found for emotion '{emotion}' or neutral. Skipping dialogue: '{dialogue}'")

    return storyboard

def assemble_final_video(storyboard: list, voice_over_path: str, music_path: str, output_path: str = "final_video.mp4"):
    """
    Assembles the final video from the storyboard, audio, and music.
    """
    try:
        print("Starting final video assembly...")

        final_clips = []
        for dialogue, clip_path in storyboard:
            video_clip = VideoFileClip(clip_path)

            txt_clip = TextClip(dialogue, fontsize=40, color='white', font='Arial-Bold',
                                stroke_color='black', stroke_width=2)
            txt_clip = txt_clip.set_position('center').set_duration(video_clip.duration)

            video_with_text = CompositeVideoClip([video_clip, txt_clip])
            final_clips.append(video_with_text)

        if not final_clips:
            print("Error: No clips were generated for the storyboard. Aborting assembly.")
            return

        final_video = CompositeVideoClip(final_clips)

        voice_over = AudioFileClip(voice_over_path)
        music = AudioFileClip(music_path)

        if music.duration < final_video.duration:
            music = music.fx(afx.audio_loop, duration=final_video.duration)

        music = music.volumex(0.2)

        final_audio = CompositeAudioClip([voice_over.set_start(0), music])
        final_audio.duration = final_video.duration

        final_video = final_video.set_audio(final_audio)
        final_video.write_videofile(output_path, codec='libx264', audio_codec='aac', fps=24)

        print(f"Successfully assembled final video at: {output_path}")

    except Exception as e:
        print(f"An error occurred during final video assembly: {e}")