import sys
from PyQt6.QtCore import QThread
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTextEdit, QFileDialog, QMessageBox, QProgressBar
)
from video_creator.logic.video_search import search_for_videos
from video_creator.gui.video_selection_window import VideoSelectionWindow
from video_creator.gui.worker import ProcessingWorker
from video_creator.logic.assembly import parse_script, create_storyboard, assemble_final_video
from video_creator.logic.voice_generation import generate_voice_audio

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI Video Creator")
        self.setGeometry(100, 100, 800, 600)
        self.selected_video_links = []
        self.voice_sample_path = ""
        self.music_path = ""
        self.analyzed_clips = []
        self.worker_thread = None
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

        # Action Buttons
        button_layout = QHBoxLayout()
        self.process_button = QPushButton("1. Find & Analyze Videos")
        self.process_button.setStyleSheet("font-size: 16px; padding: 10px;")
        self.process_button.clicked.connect(self.open_video_selection_window)

        self.assemble_button = QPushButton("2. Assemble Final Video")
        self.assemble_button.setStyleSheet("font-size: 16px; padding: 10px;")
        self.assemble_button.clicked.connect(self.start_assembly_process)
        self.assemble_button.setEnabled(False) # Disabled until clips are ready

        button_layout.addWidget(self.process_button)
        button_layout.addWidget(self.assemble_button)
        main_layout.addLayout(button_layout)

        # Progress Bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)

        self.setLayout(main_layout)

    def select_voice_sample(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Voice Sample", "", "Audio Files (*.wav *.mp3)")
        if file_path:
            self.voice_sample_path = file_path
            self.voice_sample_label.setText(file_path.split('/')[-1])

    def select_music_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Background Music", "", "Audio Files (*.wav *.mp3)")
        if file_path:
            self.music_path = file_path
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
                self.start_processing_pipeline()
            else:
                QMessageBox.information(self, "No Selection", "You did not select any videos.")
        else:
            print("User cancelled the video selection.")

    def start_processing_pipeline(self):
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0) # Indeterminate progress
        self.find_videos_button.setEnabled(False)

        self.worker_thread = QThread()
        self.worker = ProcessingWorker(self.selected_video_links)
        self.worker.moveToThread(self.worker_thread)

        self.worker.progress.connect(self.update_progress_message)
        self.worker.finished.connect(self.on_processing_finished)
        self.worker.error.connect(self.on_processing_error)

        self.worker_thread.started.connect(self.worker.run)
        self.worker_thread.finished.connect(self.worker_thread.deleteLater)

        self.worker_thread.start()

    def update_progress_message(self, message):
        print(f"Progress: {message}")
        # In a real app, we'd update a status label here.
        # For now, printing to console is sufficient.

    def on_processing_finished(self, analyzed_clips):
        self.analyzed_clips = analyzed_clips
        self.progress_bar.setVisible(False)
        self.process_button.setEnabled(True)
        QMessageBox.information(self, "Processing Complete", f"Successfully analyzed {len(self.analyzed_clips)} clips. Ready for assembly.")
        self.assemble_button.setEnabled(True) # Enable assembly button
        self.worker_thread.quit()

    def on_processing_error(self, error_message):
        self.progress_bar.setVisible(False)
        self.process_button.setEnabled(True)
        QMessageBox.critical(self, "Processing Error", error_message)
        self.worker_thread.quit()

    def start_assembly_process(self):
        script = self.script_input.toPlainText()
        if not all([script, self.voice_sample_path, self.music_path, self.analyzed_clips]):
            QMessageBox.warning(self, "Missing Information", "Please ensure you have provided a script, voice sample, music file, and have analyzed video clips.")
            return

        QMessageBox.information(self, "Assembly Started", "The application will now assemble the final video. This may take some time.")

        # This should also be in a worker thread in a real app, but for now, we run it directly
        print("\n--- Starting Final Assembly ---")

        # 1. Parse the script
        parsed = parse_script(script)

        # 2. Generate the voice-over
        print("Generating voice-over...")
        voice_over_path = generate_voice_audio(script, self.voice_sample_path)
        if not voice_over_path:
            QMessageBox.critical(self, "Error", "Failed to generate voice-over audio.")
            return

        # 3. Create the storyboard
        print("Creating storyboard...")
        storyboard = create_storyboard(parsed, self.analyzed_clips)

        # 4. Assemble the final video
        print("Assembling final video...")
        output_filename = "final_video.mp4"
        assemble_final_video(storyboard, voice_over_path, self.music_path, output_filename)

        QMessageBox.information(self, "Assembly Complete", f"Final video has been created at {output_filename}")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())