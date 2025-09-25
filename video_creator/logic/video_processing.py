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

if __name__ == '__main__':
    # Example usage for testing
    test_urls = [
        'https://www.youtube.com/watch?v=dQw4w9WgXcQ', # A well-known, stable video for testing
    ]

    print("Running video download test (first 5 seconds only)...")

    # Clean up previous downloads to ensure a fresh test
    temp_dir = "video_creator/temp/downloads"
    if os.path.exists(temp_dir):
        for f in os.listdir(temp_dir):
            os.remove(os.path.join(temp_dir, f))

    downloaded = download_videos(test_urls, test_mode=True)

    if downloaded:
        print(f"\nTest successful! Downloaded {len(downloaded)} videos:")
        for file_path in downloaded:
            print(f"- {file_path}")
            # Verify file exists
            if os.path.exists(file_path):
                print(f"  File size: {os.path.getsize(file_path)} bytes")
            else:
                print(f"  ERROR: File not found at path: {file_path}")
    else:
        print("\nTest failed. No videos were downloaded.")