import yt_dlp
import os
from moviepy.editor import VideoFileClip
import numpy as np

# --- Configuration ---
DOWNLOAD_PATH = "downloads"
CLIPS_PATH = "clips"
os.makedirs(DOWNLOAD_PATH, exist_ok=True)
os.makedirs(CLIPS_PATH, exist_ok=True)

def find_and_extract_expressive_clips(query: str, num_clips=10):
    """
    Searches YouTube for a query, downloads the top videos, finds expressive
    moments based on audio volume, and extracts them as separate video clips.

    Args:
        query (str): The search term for YouTube.
        num_clips (int): The target number of expressive clips to extract.

    Returns:
        list[str]: A list of file paths to the extracted video clips.
    """
    print(f"Starting search for '{query}'...")

    # --- 1. Search and Download Videos ---
    video_paths = search_and_download_videos(query)
    if not video_paths:
        print("Could not download any videos.")
        return []

    all_extracted_clips = []
    for video_path in video_paths:
        # --- 2. Analyze Audio to Find Loud Segments ---
        print(f"Analyzing audio for expressive moments in {video_path}...")
        loud_segments = analyze_audio_for_loud_segments(video_path)
        if not loud_segments:
            print(f"No expressive segments found in {video_path}.")
            continue

        # --- 3. Cut Video Based on Loud Segments ---
        print(f"Extracting {len(loud_segments)} clips from {video_path}...")
        extracted_clips = extract_video_segments(video_path, loud_segments)
        all_extracted_clips.extend(extracted_clips)

    print(f"Successfully extracted a total of {len(all_extracted_clips)} clips to '{CLIPS_PATH}'.")
    return all_extracted_clips

def search_and_download_videos(query: str, num_videos=3):
    """Downloads the top N search results from YouTube for a given query."""
    search_query = f"ytsearch{num_videos}:{query} anime highlights"

    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': os.path.join(DOWNLOAD_PATH, '%(title)s.%(ext)s'),
        'quiet': True,
        'ignoreerrors': True, # Continue if a video fails
    }

    downloaded_files = []
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(search_query, download=True)
            if 'entries' in info:
                for entry in info['entries']:
                    if entry: # Entry can be None if download failed
                        filename = ydl.prepare_filename(entry)
                        downloaded_files.append(filename)
                        print(f"Downloaded '{filename}'")
    except Exception as e:
        print(f"An error occurred during download: {e}")

    return downloaded_files

def analyze_audio_for_loud_segments(video_path: str, volume_threshold=0.1, segment_duration=2.0):
    """
    Analyzes the audio of a video file to find segments that exceed a volume threshold.
    Returns a list of (start_time, end_time) tuples for loud segments.
    """
    try:
        video = VideoFileClip(video_path)
        audio = video.audio
        if audio is None:
            return []

        # Get audio data as a numpy array
        # This can be memory intensive for long videos
        audio_array = audio.to_soundarray(fps=44100)

        # Using the maximum of the stereo channels for volume detection
        if audio_array.ndim > 1:
            mono_audio = np.max(np.abs(audio_array), axis=1)
        else:
            mono_audio = np.abs(audio_array)

        # Calculate RMS volume in chunks
        frame_size = int(44100 * 0.1) # 100ms chunks
        num_frames = len(mono_audio) // frame_size
        volumes = [np.sqrt(np.mean(mono_audio[i*frame_size:(i+1)*frame_size]**2)) for i in range(num_frames)]

        # Normalize volumes
        max_volume = np.max(volumes)
        if max_volume == 0: return []
        volumes = np.array(volumes) / max_volume

        # Find segments above the threshold
        loud_indices = np.where(volumes > volume_threshold)[0]
        if not loud_indices.any(): return []

        segments = []
        in_segment = False
        for i, index in enumerate(loud_indices):
            if not in_segment:
                start_time = index * 0.1 # time in seconds
                # Ensure we don't create a segment too close to a previous one
                if not segments or start_time > segments[-1][1] + 1.0:
                    segments.append((start_time, start_time + segment_duration))
                    in_segment = True
            # Check if current index is far from the start of the current segment
            if segments and (index * 0.1 > segments[-1][0] + 1.0):
                 in_segment = False

        return segments
    except Exception as e:
        print(f"Error analyzing audio: {e}")
        return []

def extract_video_segments(video_path: str, segments: list):
    """
    Extracts video segments from a video file based on a list of time tuples.
    """
    base_name = os.path.splitext(os.path.basename(video_path))[0]
    clip_paths = []
    try:
        with VideoFileClip(video_path) as video:
            for i, (start, end) in enumerate(segments):
                # Ensure segment is within video duration
                if start >= video.duration or end > video.duration:
                    continue

                output_filename = os.path.join(CLIPS_PATH, f"{base_name}_clip_{i+1}.mp4")

                # Create subclip
                new_clip = video.subclip(start, end)

                # Write to file
                new_clip.write_videofile(output_filename, codec="libx264", audio_codec="aac", logger=None)
                clip_paths.append(output_filename)
    except Exception as e:
        print(f"Error extracting video segments: {e}")
    return clip_paths

if __name__ == '__main__':
    # Example usage for testing the module directly
    test_query = "Nokotan anime"
    extracted = find_and_extract_expressive_clips(test_query)
    print(f"Extracted clips: {extracted}")