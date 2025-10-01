import yt_dlp
import os
from moviepy.editor import VideoFileClip
import numpy as np

DOWNLOAD_PATH = "downloads"
CLIPS_PATH = "clips"
os.makedirs(DOWNLOAD_PATH, exist_ok=True)
os.makedirs(CLIPS_PATH, exist_ok=True)

def get_video_info_list(query: str, max_results=20):
    """
    Gets a list of video metadata from YouTube without downloading the videos.
    This is used to build a cache for pagination.
    """
    print(f"Fetching video list for '{query}'...")
    search_query = f"ytsearch{max_results}:{query} anime highlights"
    ydl_opts = {'quiet': True, 'ignoreerrors': True, 'extract_flat': 'in_playlist'}

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(search_query, download=False)
            if 'entries' in info and info['entries']:
                return info['entries']
    except Exception as e:
        print(f"Error fetching video list: {e}")
    return []

def download_videos_from_list(video_entries: list):
    """
    Downloads videos from a provided list of yt-dlp entry dictionaries.
    """
    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': os.path.join(DOWNLOAD_PATH, '%(title)s.%(ext)s'),
        'quiet': True,
        'ignoreerrors': True,
    }

    downloaded_files = []
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        for entry in video_entries:
            if entry and entry.get('url'):
                try:
                    # Use the already extracted URL to download
                    info = ydl.extract_info(entry['url'], download=True)
                    filename = ydl.prepare_filename(info)
                    downloaded_files.append(filename)
                    print(f"Downloaded '{filename}'")
                except Exception as e:
                    print(f"Could not download {entry.get('title')}: {e}")
    return downloaded_files

def find_and_extract_expressive_clips(video_paths: list):
    """
    Takes a list of local video file paths, finds expressive moments in each,
    and extracts them as separate clips.
    """
    all_extracted_clips = []
    for video_path in video_paths:
        print(f"Analyzing audio for expressive moments in {video_path}...")
        loud_segments = analyze_audio_for_loud_segments(video_path)
        if not loud_segments:
            print(f"No expressive segments found in {video_path}.")
            continue

        print(f"Extracting {len(loud_segments)} clips from {video_path}...")
        extracted_clips = extract_video_segments(video_path, loud_segments)
        all_extracted_clips.extend(extracted_clips)

    print(f"Successfully extracted a total of {len(all_extracted_clips)} clips to '{CLIPS_PATH}'.")
    return all_extracted_clips

def analyze_audio_for_loud_segments(video_path: str, volume_threshold=0.1, segment_duration=2.0):
    try:
        with VideoFileClip(video_path) as video:
            audio = video.audio
            if audio is None: return []

            audio_array = audio.to_soundarray(fps=44100)
            if audio_array.ndim > 1:
                mono_audio = np.mean(np.abs(audio_array), axis=1)
            else:
                mono_audio = np.abs(audio_array)

            frame_size = int(44100 * 0.1)
            num_frames = len(mono_audio) // frame_size
            if num_frames == 0: return []

            volumes = [np.sqrt(np.mean(mono_audio[i*frame_size:(i+1)*frame_size]**2)) for i in range(num_frames)]
            max_volume = np.max(volumes)
            if max_volume == 0: return []

            volumes = np.array(volumes) / max_volume
            loud_indices = np.where(volumes > volume_threshold)[0]
            if not loud_indices.any(): return []

            segments = []
            in_segment = False
            for index in loud_indices:
                if not in_segment:
                    start_time = index * 0.1
                    if not segments or start_time > segments[-1][1] + 1.0:
                        segments.append((start_time, start_time + segment_duration))
                        in_segment = True
                if segments and (index * 0.1 > segments[-1][0] + 1.0):
                     in_segment = False
            return segments
    except Exception as e:
        print(f"Error analyzing audio for {video_path}: {e}")
        return []

def extract_video_segments(video_path: str, segments: list):
    base_name = os.path.splitext(os.path.basename(video_path))[0]
    clip_paths = []
    try:
        with VideoFileClip(video_path) as video:
            for i, (start, end) in enumerate(segments):
                if end > video.duration: continue
                output_filename = os.path.join(CLIPS_PATH, f"{base_name}_clip_{i+1}.mp4")
                new_clip = video.subclip(start, end)
                new_clip.write_videofile(output_filename, codec="libx264", audio_codec="aac", logger=None)
                clip_paths.append(output_filename)
    except Exception as e:
        print(f"Error extracting segments from {video_path}: {e}")
    return clip_paths