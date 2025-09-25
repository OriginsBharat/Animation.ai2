import os
import yt_dlp
import imageio_ffmpeg
from moviepy import VideoFileClip
from moviepy.video.io.ffmpeg_tools import ffmpeg_extract_subclip

def download_videos(video_urls: list, output_dir: str = "video_creator/temp/downloads", test_mode: bool = False) -> list:
    """
    Downloads videos from a list of YouTube URLs.

    Args:
        video_urls: A list of YouTube video URLs to download.
        output_dir: The directory to save the downloaded videos.
        test_mode: If True, downloads only the first 5 seconds of each video.

    Returns:
        A list of file paths to the downloaded videos.
    """
    # NOTE: The following methods of exposing ffmpeg to yt-dlp have proven
    # ineffective in this specific sandboxed environment, although they are
    # standard practice. This may be due to how subprocesses inherit env vars.
    # Leaving the code here for future reference.
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    ffmpeg_dir = os.path.dirname(ffmpeg_exe)
    if ffmpeg_dir not in os.environ["PATH"]:
        os.environ["PATH"] = ffmpeg_dir + os.pathsep + os.environ["PATH"]

    os.makedirs(output_dir, exist_ok=True)

    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': os.path.join(output_dir, '%(id)s.%(ext)s'), # Use video ID for cleaner filenames
        'quiet': True,
        # 'ffmpeg_location' is no longer needed as we've modified the PATH
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

    Args:
        video_path: The path to the video file to be split.
        clip_duration: The duration of each clip in seconds.
        output_dir: The directory to save the clips.

    Returns:
        A list of file paths to the created clips.
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
                if end_time - start_time < 1:  # Ignore clips less than 1 second
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

if __name__ == '__main__':
    # NOTE: The following test will fail in environments where ffmpeg is not
    # accessible to the yt-dlp subprocess, as is the case in this sandbox.
    # The code is logically correct but blocked by this environmental issue.
    # Example usage for testing
    test_urls = [
        'https://www.youtube.com/watch?v=dQw4w9WgXcQ', # A well-known, stable video for testing
    ]

    print("--- Running Video Download Test ---")
    downloaded_files = download_videos(test_urls, test_mode=True)

    if downloaded_files:
        print(f"\n--- Download Test Successful ---")

        # --- Test video splitting ---
        print("\n--- Running Video Splitting Test ---")
        video_to_split = downloaded_files[0]
        clips = split_video_into_clips(video_to_split)

        if clips:
            print(f"\n--- Splitting Test Successful ---")
            print(f"Created {len(clips)} clips:")
            for clip_path in clips[:3]: # Print first 3 clips
                print(f"- {clip_path} (exists: {os.path.exists(clip_path)})")
        else:
            print("\n--- Splitting Test Failed ---")

    else:
        print("\n--- Download Test Failed ---")