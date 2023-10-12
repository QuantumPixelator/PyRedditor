import praw
import json
import requests
import os
from PySide6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QLabel, QLineEdit, QSlider, QComboBox, QPushButton, QWidget, QHBoxLayout, QFileDialog, QMessageBox)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QPalette, QColor, QFont, QIcon

class RedditDownloader(QThread):
    progress_signal = Signal(int)
    error_signal = Signal(str)
    processing_signal = Signal(str)

    def __init__(self, reddit, subreddit_list, sort_by, limit, time_filter, save_path):
        super().__init__()
        self.reddit = reddit
        self.subreddit_list = subreddit_list
        self.sort_by = sort_by
        self.limit = limit
        self.time_filter = time_filter
        self.save_path = save_path
        self.is_running = True
        self.failed_subreddits = []
        self.total_downloads = 0

    def run(self):
        for subreddit_name in self.subreddit_list:
            if not self.is_running:
                break
            self.processing_signal.emit(subreddit_name)
            subreddit_save_path = os.path.join(self.save_path, subreddit_name)
            if not os.path.exists(subreddit_save_path):
                os.makedirs(subreddit_save_path)
            try:
                subreddit = self.reddit.subreddit(subreddit_name)
                submissions = getattr(subreddit, self.sort_by)(limit=self.limit) if self.sort_by not in ["top", "controversial"] else getattr(subreddit, self.sort_by)(limit=self.limit, time_filter=self.time_filter)
                for submission in submissions:
                    if not self.is_running:
                        break
                    if not submission.is_self and 'url' in vars(submission):
                        url = submission.url
                        if url.endswith(('.jpg', '.jpeg', '.png', '.gif', '.gifv', '.webm', '.mp4', '.webp')):
                            response = requests.get(url)
                            with open(os.path.join(subreddit_save_path, os.path.basename(url)), 'wb') as file:
                                file.write(response.content)
                            self.total_downloads += 1
                            self.progress_signal.emit(1)
            except:
                self.failed_subreddits.append(subreddit_name)
        if self.failed_subreddits:
            self.error_signal.emit(", ".join(self.failed_subreddits))
        self.processing_signal.emit("Processing Complete")

    def stop(self):
        self.is_running = False

class RedditMediaDownloader(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyRedditor")
        self.setWindowIcon(QIcon("icon.png"))
        self.resize(320, 290)

        palette = QPalette()
        palette.setColor(QPalette.Window, Qt.white)
        palette.setColor(QPalette.WindowText, Qt.black)
        palette.setColor(QPalette.Button, QColor(255, 165, 0))
        palette.setColor(QPalette.ButtonText, Qt.white)
        palette.setColor(QPalette.Highlight, QColor(255, 165, 0))
        palette.setColor(QPalette.HighlightedText, Qt.white)
        self.setPalette(palette)
        
        self.setStyleSheet("""
            QPushButton {
                background-color: #FF4500;
                color: white;
                border-radius: 7px;
                height: 25px;
            }
            QPushButton:hover {
                background-color: #FF5722;
            }
            QPushButton:disabled {
                background-color: gray;
                color: black;
            }
            QComboBox {
                border-radius: 7px;
                background-color: #FF4500;
                color: white;
                height: 25px;
            }
            QLineEdit {
                border-radius: 7px;
                background-color: white;
                color: #FF4500;
                border: 2px solid #FF4500;
            }
            QSlider::handle:horizontal {
                height: 10px;
                background: #FF4500;
                margin: 0 -4px;
            }
        """)

        main_layout = QVBoxLayout()
        self.header_label = QLabel("PyRedditor", self)
        self.header_label.setFont(QFont("Courier New", 20, QFont.Bold))
        self.header_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.header_label, alignment=Qt.AlignCenter)

        self.mini_label = QLabel("Reddit Image Scraper\n\n", self)
        font = QFont("Verdana",7)
        font.setItalic(True)
        self.mini_label.setFont(font)
        self.mini_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.mini_label, alignment=Qt.AlignCenter)

        self.load_button = QPushButton("Load Subreddits From File")
        main_layout.addWidget(self.load_button)

        self.limit_label = QLabel("Limit: 50")
        main_layout.addWidget(self.limit_label)
        self.limit_slider = QSlider(Qt.Horizontal)
        self.limit_slider.setMinimum(1)
        self.limit_slider.setMaximum(100)
        self.limit_slider.setValue(50)
        self.limit_slider.valueChanged.connect(self.update_slider_value)
        main_layout.addWidget(self.limit_slider)

        sort_hbox = QHBoxLayout()
        sort_vbox = QVBoxLayout()
        self.sort_label = QLabel("Sort by:")
        sort_vbox.addWidget(self.sort_label)
        self.sort_combobox = QComboBox()
        self.sort_combobox.addItems(["top", "new", "hot", "rising"])
        sort_vbox.addWidget(self.sort_combobox)

        time_vbox = QVBoxLayout()
        self.time_label = QLabel("Time Filter:")
        time_vbox.addWidget(self.time_label)
        self.time_combobox = QComboBox()
        self.time_combobox.addItems(["all", "year", "month", "week", "day", "hour"])
        time_vbox.addWidget(self.time_combobox)

        sort_hbox.addLayout(sort_vbox)
        sort_hbox.addLayout(time_vbox)
        main_layout.addLayout(sort_hbox)

        self.start_button = QPushButton("Start Download")
        main_layout.addWidget(self.start_button)

        self.stop_button = QPushButton("Stop Download")
        self.stop_button.setEnabled(False)
        main_layout.addWidget(self.stop_button)

        self.downloaded_label = QLabel("Downloads Saved: 0")
        self.downloaded_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.downloaded_label)

        # Add a stretch to push subsequent widgets to the bottom
        main_layout.addStretch(1)

        # Add the processing label after the stretch
        self.processing_label = QLabel("Waiting to start...", self)
        self.processing_label.setAlignment(Qt.AlignCenter)  # Center the text in the label
        main_layout.addWidget(self.processing_label)

        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)


        self.load_button.clicked.connect(self.load_subreddits_from_file)
        self.start_button.clicked.connect(self.start_download)
        self.stop_button.clicked.connect(self.stop_download)

        self.reddit_thread = None

        self.cred_path = "credentials.json"
        if os.path.exists(self.cred_path):
            with open(self.cred_path) as f:
                self.cred = json.load(f)
        else:
            raise ValueError("credentials.json file not found. Please ensure the file exists with correct credentials.")

    def load_subreddits_from_file(self):
        options = QFileDialog.Options()
        fileName, _ = QFileDialog.getOpenFileName(self, "Select Subreddit List File", "", "Text Files (*.txt)", options=options)
        if fileName:
            with open(fileName, 'r') as f:
                self.subreddit_list = [line.strip() for line in f.readlines()]

    def start_download(self):
        if not hasattr(self, 'subreddit_list'):
            QMessageBox.warning(self, 'Warning', 'Please load a subreddit list file first.')
            return

        self.downloaded_label.setText("Downloads Saved: 0")
        sort = self.sort_combobox.currentText()
        limit = self.limit_slider.value()
        when = self.time_combobox.currentText()

        reddit = praw.Reddit(**self.cred)

        self.reddit_thread = RedditDownloader(reddit, self.subreddit_list, sort, limit, when, "images")
        self.reddit_thread.progress_signal.connect(self.update_progress)
        self.reddit_thread.error_signal.connect(self.show_errors)
        self.reddit_thread.processing_signal.connect(self.show_processing)
        self.reddit_thread.finished.connect(self.job_complete)
        self.reddit_thread.start()

        self.downloaded_label.setStyleSheet("color: green; font-weight: bold;")
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)

    def stop_download(self):
        if self.reddit_thread:
            self.reddit_thread.stop()
        self.reset_ui()

    def job_complete(self):
        self.reset_ui()
        summary_msg = f"Total images downloaded: {self.reddit_thread.total_downloads}"
        if self.reddit_thread.failed_subreddits:
            summary_msg += f"\nFailed to process the following subreddits: {', '.join(self.reddit_thread.failed_subreddits)}"
        QMessageBox.information(self, 'Job Complete', summary_msg)

    def reset_ui(self):
        self.processing_label.setText("Processing Complete")
        self.downloaded_label.setStyleSheet("color: black; font-weight: normal;")
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)

    def update_progress(self, count):
        self.downloaded_label.setText(f"Downloads Saved: {self.reddit_thread.total_downloads}")

    def show_errors(self, errors):
        self.processing_label.setText(f"Errors encountered with: {errors}")

    def show_processing(self, subreddit_name):
        self.processing_label.setText(f"Processing: {subreddit_name}")

    def update_slider_value(self, value):
        self.limit_label.setText(f"Limit: {value}")

if __name__ == "__main__":
    app = QApplication([])
    window = RedditMediaDownloader()
    window.show()
    app.exec()
