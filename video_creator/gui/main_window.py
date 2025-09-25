import sys
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTextEdit, QFileDialog, QMessageBox
)
from video_creator.logic.video_search import search_for_videos
from video_creator.gui.video_selection_window import VideoSelectionWindow

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI Video Creator")
        self.setGeometry(100, 100, 800, 600)
        self.selected_video_links = []
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
                print(f"User selected {len(self.selected_video_links)} videos: {self.selected_video_links}")
                # Here we would trigger the next step (downloading and processing)
            else:
                print("User closed the selection window without choosing any videos.")
        else:
            print("User cancelled the video selection.")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())