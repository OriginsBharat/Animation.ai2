import os
import yt_dlp
from moviepy.editor import VideoFileClip
from moviepy.video.io.ffmpeg_tools import ffmpeg_extract_subclip
import imageio_ffmpeg

def download_videos(video_urls: list, output_dir: str = "video_creator/temp/downloads", test_mode: bool = False) -> list:
    """
    Downloads videos from a list of YouTube URLs.
    """
    os.makedirs(output_dir, exist_ok=True)

    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': os.path.join(output_dir, '%(id)s.%(ext)s'),
        'quiet': True,
    }

    if test_mode:
        ydl_opts['download_ranges'] = lambda info_dict, ydl: [{'start_time': 0, 'end_time': 5}]

    downloaded_files = []
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        for url in video_urls:
            try:
                print(f"Downloading video clip: {url}")
                info_dict = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info_dict)
                downloaded_files.append(filename)
                print(f"Successfully downloaded to {filename}")
            except Exception as e:
                print(f"Error downloading {url}: {e}")

    return downloaded_files

def split_video_into_clips(video_path: str, clip_duration: int = 3, output_dir: str = "video_creator/temp/clips") -> list:
    """
    Splits a video into smaller clips of a fixed duration.
    """
    if not os.path.exists(video_path):
        print(f"Error: Video file not found at {video_path}")
        return []

    video_filename = os.path.splitext(os.path.basename(video_path))[0]
    clip_output_dir = os.path.join(output_dir, video_filename)
    os.makedirs(clip_output_dir, exist_ok=True)

    try:
        with VideoFileClip(video_path) as video:
            duration = video.duration
            clip_paths = []
            for i in range(0, int(duration), clip_duration):
                start_time = i
                end_time = min(i + clip_duration, duration)
                if end_time - start_time < 1:
                    continue

                clip_filename = f"clip_{start_time:04d}_{end_time:04d}.mp4"
                clip_path = os.path.join(clip_output_dir, clip_filename)

                ffmpeg_extract_subclip(video_path, start_time, end_time, targetname=clip_path)
                clip_paths.append(clip_path)

            print(f"Split {video_path} into {len(clip_paths)} clips.")
            return clip_paths
    except Exception as e:
        print(f"Error splitting video {video_path}: {e}")
        return []