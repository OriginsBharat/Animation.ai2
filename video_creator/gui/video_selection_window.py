import sys
import requests
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QCheckBox, QScrollArea, QDialog
)
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt

class VideoSelectionWindow(QDialog):
    def __init__(self, video_list, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Videos to Download")
        self.setGeometry(150, 150, 900, 700)
        self.video_list = video_list
        self.selected_videos = []
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()

        scroll_area = QScrollArea()
        scroll_widget = QWidget()
        self.scroll_layout = QVBoxLayout(scroll_widget)

        for video_info in self.video_list:
            video_widget = self.create_video_widget(video_info)
            self.scroll_layout.addWidget(video_widget)

        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)
        main_layout.addWidget(scroll_area)

        self.download_button = QPushButton("Download & Analyze Selected Videos")
        self.download_button.clicked.connect(self.accept)
        main_layout.addWidget(self.download_button)

        self.setLayout(main_layout)

    def create_video_widget(self, video_info):
        widget = QWidget()
        layout = QHBoxLayout(widget)

        # Thumbnail
        thumbnail_label = QLabel()
        if video_info['thumbnails']:
            url = video_info['thumbnails'][0]['url']
            try:
                response = requests.get(url)
                pixmap = QPixmap()
                pixmap.loadFromData(response.content)
                thumbnail_label.setPixmap(pixmap.scaled(120, 90, Qt.AspectRatioMode.KeepAspectRatio))
            except Exception as e:
                thumbnail_label.setText("No Thumbnail")
                print(f"Could not load thumbnail for {video_info['title']}: {e}")
        else:
            thumbnail_label.setText("No Thumbnail")

        # Title
        title_label = QLabel(f"<b>{video_info['title']}</b>")
        title_label.setWordWrap(True)

        # Checkbox
        checkbox = QCheckBox()
        checkbox.stateChanged.connect(lambda state, link=video_info['link']: self.toggle_video_selection(state, link))

        layout.addWidget(checkbox)
        layout.addWidget(thumbnail_label)
        layout.addWidget(title_label)
        layout.addStretch()

        return widget

    def toggle_video_selection(self, state, link):
        if state == Qt.CheckState.Checked.value and link not in self.selected_videos:
            self.selected_videos.append(link)
        elif state == Qt.CheckState.Unchecked.value and link in self.selected_videos:
            self.selected_videos.remove(link)

    def get_selected_videos(self):
        return self.selected_videos

if __name__ == '__main__':
    # Example usage for testing
    app = QApplication(sys.argv)

    # Dummy data similar to what our search function provides
    dummy_videos = [
        {'title': 'Funny Cat Video 1', 'link': 'https://www.youtube.com/watch?v=111', 'thumbnails': [{'url': 'https://i.ytimg.com/vi/3URtTIdnXIk/hq720.jpg'}]},
        {'title': 'Cute Kitten Moments', 'link': 'https://www.youtube.com/watch?v=222', 'thumbnails': [{'url': 'https://i.ytimg.com/vi/B4MzQDwz6mE/hq720.jpg'}]},
        {'title': 'Torako Being Hilarious', 'link': 'https://www.youtube.com/watch?v=333', 'thumbnails': [{'url': 'https://i.ytimg.com/vi/QcVSOI8hv3M/hq720.jpg'}]}
    ]

    dialog = VideoSelectionWindow(dummy_videos)
    if dialog.exec():
        selected = dialog.get_selected_videos()
        print(f"User selected the following videos for download: {selected}")
    else:
        print("User cancelled the selection.")

    sys.exit()