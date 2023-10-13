import praw
import json
import requests
import os
from PySide6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QLabel, QLineEdit, QSlider, QComboBox, QPushButton, QWidget, QHBoxLayout, QFileDialog, QMessageBox)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QPalette, QColor, QFont, QIcon

class RedditDownloader(QThread):
    progress_signal = Signal(int, str)
    job_complete_signal = Signal(list)

    def __init__(self, reddit, subreddit_list, sort_by, limit, time_filter, save_path):
        super().__init__()
        self.reddit = reddit
        self.subreddit_list = subreddit_list
        self.sort_by = sort_by
        self.limit = limit
        self.time_filter = time_filter
        self.save_path = save_path
        self.is_running = True
        self.total_downloads = 0
        self.error_subreddits = []

    def run(self):
        for subreddit_name in self.subreddit_list:
            if not self.is_running:
                break
            try:
                self.progress_signal.emit(self.total_downloads, f"Processing: {subreddit_name}")
                subreddit_save_path = os.path.join(self.save_path, subreddit_name)
                if not os.path.exists(subreddit_save_path):
                    os.makedirs(subreddit_save_path)

                subreddit = self.reddit.subreddit(subreddit_name)

                if self.sort_by in ["top", "controversial"]:
                    submissions = getattr(subreddit, self.sort_by)(limit=self.limit, time_filter=self.time_filter)
                else:
                    submissions = getattr(subreddit, self.sort_by)(limit=self.limit)

                for submission in submissions:
                    if not self.is_running:
                        break

                    if not submission.is_self and 'url' in vars(submission):
                        url = submission.url
                        if url.endswith(('.jpg', '.jpeg', '.png')):
                            response = requests.get(url)
                            with open(os.path.join(subreddit_save_path, os.path.basename(url)), 'wb') as file:
                                file.write(response.content)
                            self.total_downloads += 1
                            self.progress_signal.emit(self.total_downloads, f"Processing: {subreddit_name}")

            except Exception as e:
                self.error_subreddits.append(subreddit_name)

        self.job_complete_signal.emit(self.error_subreddits)

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
        self.downloaded_label.setStyleSheet("color: green; font-weight: bold;")
        main_layout.addWidget(self.downloaded_label)

        self.status_label = QLabel("Status: Idle")
        main_layout.addWidget(self.status_label)

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

        sort = self.sort_combobox.currentText()
        limit = self.limit_slider.value()
        when = self.time_combobox.currentText()

        reddit = praw.Reddit(**self.cred)

        self.reddit_thread = RedditDownloader(reddit, self.subreddit_list, sort, limit, when, "images")
        self.reddit_thread.progress_signal.connect(self.update_progress)
        self.reddit_thread.job_complete_signal.connect(self.job_complete)
        self.reddit_thread.start()

        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)

    def stop_download(self):
        if self.reddit_thread:
            self.reddit_thread.stop()
        self.reset_ui()

    def job_complete(self, error_subreddits):
        self.reset_ui()
        if error_subreddits:
            error_text = f"Subreddits with errors: {', '.join(error_subreddits)}"
        else:
            error_text = "No errors encountered."
        QMessageBox.information(self, 'Job Complete', f'Total images downloaded: {self.reddit_thread.total_downloads}\n{error_text}')

    def reset_ui(self):
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.status_label.setText("Status: Idle")

    def update_progress(self, count, status_text):
        self.downloaded_label.setText(f"Downloads Saved: {count}")
        self.status_label.setText(status_text)

    def update_slider_value(self, value):
        self.limit_label.setText(f"Limit: {value}")

if __name__ == "__main__":
    app = QApplication([])
    window = RedditMediaDownloader()
    window.show()
    app.exec_()
