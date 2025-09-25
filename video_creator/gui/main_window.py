import sys
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTextEdit, QFileDialog, QMessageBox
)
from video_creator.logic.video_search import search_for_videos
from video_creator.gui.video_selection_window import VideoSelectionWindow
from video_creator.logic.video_processing import download_videos, split_video_into_clips
from video_creator.logic.ai_analysis import analyze_clip_emotion

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI Video Creator")
        self.setGeometry(100, 100, 800, 600)
        self.selected_video_links = []
        self.analyzed_clips = []  # This will store {'path': '...', 'emotion': '...'}
        self.init_ui()

    def init_ui(self):
        # Main layout
        main_layout = QVBoxLayout()

        # Search Keywords
        search_layout = QHBoxLayout()
        search_label = QLabel("Search Keywords:")
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("e.g., 'Nokotan funny moments'")
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_input)
        main_layout.addLayout(search_layout)

        # File Pickers
        file_picker_layout = QHBoxLayout()
        self.voice_sample_button = QPushButton("Select Voice Sample")
        self.voice_sample_button.clicked.connect(self.select_voice_sample)
        self.voice_sample_label = QLabel("No file selected.")

        self.music_file_button = QPushButton("Select Background Music")
        self.music_file_button.clicked.connect(self.select_music_file)
        self.music_file_label = QLabel("No file selected.")

        file_picker_layout.addWidget(self.voice_sample_button)
        file_picker_layout.addWidget(self.voice_sample_label)
        file_picker_layout.addStretch()
        file_picker_layout.addWidget(self.music_file_button)
        file_picker_layout.addWidget(self.music_file_label)
        main_layout.addLayout(file_picker_layout)

        # Script Text Area
        script_label = QLabel("Script:")
        self.script_input = QTextEdit()
        self.script_input.setPlaceholderText("Enter your script here, with emotional cues in parentheses, e.g., 'This is amazing! (HAPPY)'")
        main_layout.addWidget(script_label)
        main_layout.addWidget(self.script_input)

        # Main Action Button
        self.find_videos_button = QPushButton("Find Videos")
        self.find_videos_button.setStyleSheet("font-size: 16px; padding: 10px;")
        self.find_videos_button.clicked.connect(self.open_video_selection_window)
        main_layout.addWidget(self.find_videos_button)

        self.setLayout(main_layout)

    def select_voice_sample(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Voice Sample", "", "Audio Files (*.wav *.mp3)")
        if file_path:
            self.voice_sample_label.setText(file_path.split('/')[-1])

    def select_music_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Background Music", "", "Audio Files (*.wav *.mp3)")
        if file_path:
            self.music_file_label.setText(file_path.split('/')[-1])

    def open_video_selection_window(self):
        keywords = self.search_input.text()
        if not keywords:
            QMessageBox.warning(self, "Warning", "Please enter search keywords.")
            return

        videos = search_for_videos(keywords)
        if not videos:
            QMessageBox.information(self, "No Results", f"No videos found for '{keywords}'.")
            return

        selection_dialog = VideoSelectionWindow(videos, self)
        if selection_dialog.exec():
            self.selected_video_links = selection_dialog.get_selected_videos()
            if self.selected_video_links:
                self.start_processing_pipeline(self.selected_video_links)
            else:
                QMessageBox.information(self, "No Selection", "You did not select any videos.")
        else:
            print("User cancelled the video selection.")

    def start_processing_pipeline(self, video_urls):
        QMessageBox.information(self, "Processing Started", "The application will now download, split, and analyze the selected videos. This may take some time.")

        # Step 1: Download videos
        # NOTE: Using test_mode=True because of the ffmpeg issue in the sandbox.
        # This will likely still fail, but it's required to test the pipeline flow.
        print("\n--- Starting Video Processing Pipeline ---")
        print("\nStep 1: Downloading videos...")
        downloaded_paths = download_videos(video_urls, test_mode=True)
        if not downloaded_paths:
            QMessageBox.critical(self, "Error", "Video download failed. Please check the console. Cannot proceed.")
            return
        print(f"Downloaded {len(downloaded_paths)} video files.")

        # Step 2: Split videos into clips
        print("\nStep 2: Splitting videos into clips...")
        all_clips = []
        for path in downloaded_paths:
            clips = split_video_into_clips(path)
            all_clips.extend(clips)

        if not all_clips:
            QMessageBox.critical(self, "Error", "Video splitting failed. No clips were created. Please check the console.")
            return
        print(f"Created a total of {len(all_clips)} clips.")

        # Step 3: Analyze emotions in clips
        print("\nStep 3: Analyzing emotions in clips...")
        for clip_path in all_clips:
            emotion = analyze_clip_emotion(clip_path)
            self.analyzed_clips.append({'path': clip_path, 'emotion': emotion})

        print(f"Analyzed {len(self.analyzed_clips)} clips successfully.")
        QMessageBox.information(self, "Processing Complete", f"Successfully analyzed {len(self.analyzed_clips)} clips and they are ready for video assembly.")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())