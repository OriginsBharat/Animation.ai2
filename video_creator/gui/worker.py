from PyQt6.QtCore import QObject, pyqtSignal
from video_creator.logic.video_processing import download_videos, split_video_into_clips
from video_creator.logic.ai_analysis import analyze_clip_emotion

class ProcessingWorker(QObject):
    """
    A worker to handle the video processing pipeline in a separate thread.
    """
    progress = pyqtSignal(str)
    finished = pyqtSignal(list)
    error = pyqtSignal(str)

    def __init__(self, video_urls):
        super().__init__()
        self.video_urls = video_urls

    def run(self):
        """
        Executes the full processing pipeline.
        """
        try:
            # Step 1: Download videos
            self.progress.emit("Downloading videos...")
            downloaded_paths = download_videos(self.video_urls, test_mode=False)
            if not downloaded_paths:
                self.error.emit("Video download failed. Please check the console.")
                return

            # Step 2: Split videos into clips
            self.progress.emit("Splitting videos into clips...")
            all_clips = []
            for path in downloaded_paths:
                clips = split_video_into_clips(path)
                all_clips.extend(clips)

            if not all_clips:
                self.error.emit("Video splitting failed. No clips were created.")
                return

            # Step 3: Analyze emotions in clips
            analyzed_clips = []
            total_clips = len(all_clips)
            for i, clip_path in enumerate(all_clips):
                self.progress.emit(f"Analyzing clip {i+1} of {total_clips}...")
                emotion = analyze_clip_emotion(clip_path)
                analyzed_clips.append({'path': clip_path, 'emotion': emotion})

            self.progress.emit("Analysis complete!")
            self.finished.emit(analyzed_clips)

        except Exception as e:
            self.error.emit(f"An unexpected error occurred: {e}")