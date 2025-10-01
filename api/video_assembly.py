import os
from moviepy.editor import (
    VideoFileClip,
    AudioFileClip,
    concatenate_videoclips,
    TextClip,
    CompositeVideoClip,
    ImageClip,
    ColorClip,
)
import moviepy.video.fx.all as vfx
import re
import numpy as np
from PIL import Image, ImageDraw

OUTPUT_PATH = "outputs"
os.makedirs(OUTPUT_PATH, exist_ok=True)

def parse_script_for_subtitles(script_text: str, audio_duration: float):
    lines = [line.strip() for line in script_text.split('\n') if line.strip()]
    if not lines:
        return []

    num_lines = len(lines)
    duration_per_line = audio_duration / num_lines
    subtitles = []

    for i, line in enumerate(lines):
        start_time = i * duration_per_line
        clean_line = re.sub(r'\(.*?\)', '', line).strip()

        fontsize = 70
        font = "Arial-Bold"
        color = "white"
        stroke_color = "black"
        stroke_width = 3

        if clean_line.isupper() and len(clean_line) > 1:
            fontsize = 75

        txt_clip = (
            TextClip(
                clean_line,
                fontsize=fontsize,
                color=color,
                font=font,
                stroke_color=stroke_color,
                stroke_width=stroke_width,
                method="caption",
                size=(1000, None),
            )
            .set_position(("center", 0.8), relative=True)
            .set_duration(duration_per_line)
            .set_start(start_time)
        )
        subtitles.append(txt_clip)

    return subtitles

def apply_stylized_effects(clip, size=(1080, 1080)):
    # Resize and crop to a square format
    clip = vfx.crop(clip.fx(vfx.resize, height=size[1]), width=size[0], height=size[1], x_center=clip.w/2, y_center=clip.h/2)

    # Apply a warm, slightly desaturated color filter
    clip = clip.fx(vfx.colorx, factor=1.1).fx(vfx.colorx, factor=[1.05, 1.02, 0.95])

    # Create a rounded rectangle mask
    radius = 100
    mask_img = Image.new("L", size, 0)
    draw = ImageDraw.Draw(mask_img)
    draw.rounded_rectangle((0, 0, size[0], size[1]), radius=radius, fill=255)

    mask_clip = ImageClip(np.array(mask_img), ismask=True)

    clip.set_mask(mask_clip)
    return clip

def assemble_video(
    clip_paths: list[str],
    final_audio_path: str,
    script_text: str,
    output_filename: str = "final_video.mp4",
    apply_effects: bool = True,
):
    if not clip_paths or not final_audio_path:
        print("Error: Missing video clips or audio file.")
        return None

    try:
        print("--- Starting Video Assembly ---")

        final_audio = AudioFileClip(final_audio_path)
        audio_duration = final_audio.duration

        video_clips = []
        for path in clip_paths:
            clip = VideoFileClip(path)
            if apply_effects:
                clip = apply_stylized_effects(clip)
            video_clips.append(clip)

        concatenated_clips = concatenate_videoclips(video_clips, method="compose")

        if concatenated_clips.duration > audio_duration:
            final_video = concatenated_clips.subclip(0, audio_duration)
        elif concatenated_clips.duration < audio_duration:
            duration_to_fill = audio_duration - concatenated_clips.duration
            looped_last_clip = video_clips[-1].fx(vfx.loop, duration=duration_to_fill)
            final_video = concatenate_videoclips([concatenated_clips, looped_last_clip])
        else:
            final_video = concatenated_clips

        final_video = final_video.set_audio(final_audio)
        subtitles = parse_script_for_subtitles(script_text, audio_duration)

        # Create a black background clip
        background = ColorClip(size=(1080, 1920), color=(0,0,0), duration=audio_duration)

        # Composite the final video on top of the black background
        final_composition = CompositeVideoClip([background, final_video.set_position('center')] + subtitles)

        output_path = os.path.join(OUTPUT_PATH, output_filename)
        final_composition.write_videofile(
            output_path,
            codec="libx264",
            audio_codec="aac",
            temp_audiofile="temp-audio.m4a",
            remove_temp=True,
            logger="bar",
        )

        final_audio.close()
        for clip in video_clips:
            clip.close()

        print(f"--- Video Assembly Complete. Saved to: {output_path} ---")
        return output_path

    except Exception as e:
        print(f"An error occurred during video assembly: {e}")
        return None