# gui.py
import os
import io
import dotenv
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QTextEdit, QLabel, 
    QFileDialog, QMenuBar, QAction, 
    QMainWindow, QMessageBox, QSpacerItem, 
    QSizePolicy, QComboBox,
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont
from pygame import mixer  # For playing audio

# Import necessary API stuff for the main class
from api.emotions_api import detect_emotions
from api.elevenlabs_api import change_voice_model, voice_models

# Import the workers and constructors
from workers import QueryWorker, SpeechRecognitionWorker, ElevenLabsAudioWorker
from construct import ChatHistoryDialog

# Initialize pygame mixer for audio playback
mixer.init()

dotenv.load_dotenv()

# Main application window
class AlterEgo(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ALTER EGO")
        self.setGeometry(100, 100, 1920, 1080)
        self.setMinimumSize(1280, 720)
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        self.layout = QVBoxLayout()

        # Character loading and active character display
        button_and_label_layout = QVBoxLayout()
        self.load_button = QPushButton("Load Character")
        self.load_button.setFixedSize(150, 50)
        self.load_button.setObjectName("loadButton")
        self.load_button.clicked.connect(self.load_character)
        button_and_label_layout.addWidget(self.load_button, alignment=Qt.AlignLeft)

        # Displays the active character being used
        self.active_character_label = QLabel(f"Active Character: Loading...", self)
        italic_font = QFont('Courier New', 16)
        italic_font.setItalic(True)
        self.active_character_label.setFont(italic_font)
        button_and_label_layout.addWidget(self.active_character_label, alignment=Qt.AlignLeft)
        self.layout.addLayout(button_and_label_layout)

        # Query input and buttons (Send Query)
        input_and_button_layout = QHBoxLayout()
        self.query_input = QTextEdit()
        self.query_input.setFont(QFont('Courier New', 14))
        self.query_input.setPlaceholderText("Type your query here...")
        self.query_input.setFixedHeight(75)
        input_and_button_layout.addWidget(self.query_input)

        # Send Query button
        self.send_button = QPushButton("Send Query")
        self.send_button.setFixedSize(150, 50)
        self.send_button.setObjectName("sendButton")
        self.send_button.clicked.connect(self.send_query)
        input_and_button_layout.addWidget(self.send_button)

        self.layout.addLayout(input_and_button_layout)

        # Response display area
        self.response_label = QLabel("Response:")
        self.response_label.setFont(QFont('Courier New', 14))
        self.response_display = QTextEdit()
        self.response_display.setFont(QFont('Courier New', 14))
        self.response_display.setReadOnly(True)
        self.layout.addWidget(self.response_label)
        self.layout.addWidget(self.response_display)

        # Add emotions display box in the bottom left corner
        emotions_layout = QHBoxLayout()
        self.emotions_label = QLabel("Detected Emotions:")
        self.emotions_label.setFont(QFont('Courier New', 14))
        self.emotions_display = QTextEdit()
        self.emotions_display.setFont(QFont('Courier New', 14))
        self.emotions_display.setReadOnly(True)
        self.emotions_display.setFixedHeight(100)
        self.emotions_display.setFixedWidth(300)
        self.emotions_display.setObjectName("emotionsDisplay")

        emotions_layout.addWidget(self.emotions_label)
        emotions_layout.addWidget(self.emotions_display)
        emotions_layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))

        self.layout.addLayout(emotions_layout)

        # Speech Recognition status label
        self.speech_status_label = QLabel("Speech Recognition (F4): OFF")
        self.speech_status_label.setFont(QFont('Courier New', 14))
        self.speech_status_label.setStyleSheet("color: red;")  # Default to red (OFF)
        self.layout.addWidget(self.speech_status_label)

        # Voice Model Selection (properly aligned on the left)
        voice_model_layout = QHBoxLayout()
        self.voice_model_label = QLabel("Voice Model:")
        self.voice_model_label.setFont(QFont('Courier New', 14))
        voice_model_layout.addWidget(self.voice_model_label)

        self.voice_model_combo = QComboBox()
        combo_font = QFont('Courier New', 14)  # Match font size of label
        self.voice_model_combo.setFont(combo_font)  # Apply the font to combo box
        self.voice_model_combo.addItems(voice_models.keys())
        self.voice_model_combo.currentTextChanged.connect(self.on_voice_model_changed)
        voice_model_layout.addWidget(self.voice_model_combo)

        voice_model_layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))  # Spacer to push combo box to the left

        self.layout.addLayout(voice_model_layout)  # Add layout to the main window

        central_widget.setLayout(self.layout)

        # Menu setup
        self.menu_bar = QMenuBar(self)
        self.setMenuBar(self.menu_bar)
        self.menu = self.menu_bar.addMenu("☰")

        # Chat History
        self.chat_history_action = QAction("Chat History", self)
        self.chat_history_action.triggered.connect(self.open_chat_history)
        self.menu.addAction(self.chat_history_action)

        # Fullscreen
        self.fullscreen_action = QAction("Toggle Fullscreen", self)
        self.fullscreen_action.triggered.connect(self.toggle_fullscreen)
        self.menu.addAction(self.fullscreen_action)

        # Add ElevenLabs Audio Toggle to the menu
        self.audio_checkbox_action = QAction("Enable ElevenLabs Speech Audio", self, checkable=True)
        self.audio_checkbox_action.setChecked(True)  # Default ON
        self.menu.addAction(self.audio_checkbox_action)

        self.character_file = None
        self.character_data = None
        self.animation_timer = QTimer(self)
        self.animation_timer.timeout.connect(self.update_text_animation)
        self.animated_text = ""
        self.current_text_index = 0
        self.fullscreen = False
        self.speech_recognition_worker = None
        self.load_default_character()

        # Stylesheet for UI elements
        self.setStyleSheet("""
            QWidget {
                background-color: black;
                color: #00FF00;
                font-family: 'Courier New', monospace;
            }
            QPushButton {
                background-color: black;
                color: #00FF00;
                border: 1px solid #00FF00;
                padding: 5px;
                font-size: 14px;
            }
            QPushButton#loadButton {
                font-size: 14px;
            }
            QPushButton#sendButton {
                font-size: 15px;
            }
            QPushButton:hover {
                background-color: #00FF00;
                color: black;
            }
            QTextEdit {
                background-color: black;
                color: #00FF00;
                border: 1px solid #00FF00;
            }
            QTextEdit#emotionsDisplay {
                color: red;  /* Set detected emotions text color to red */
            }
            QLabel {
                color: #00FF00;
            }
            QMenuBar {
                background-color: black;
                color: #00FF00;
            }
            QMenuBar::item {
                background-color: black;
                color: #00FF00;
            }
            QMenuBar::item:selected {
                background-color: #00FF00;
                color: black;
            }
        """)

    def load_default_character(self):
        default_character_file = "DEFAULT"
        character_path = os.path.join(os.path.dirname(__file__), 'characterdata', f"{default_character_file}.chr")
        if os.path.exists(character_path):
            with open(character_path, 'r') as file:
                self.character_file = default_character_file
                self.character_data = file.read()
                self.update_active_character_label()
        else:
            self.show_system_message("Default character file not found.", "Error")
            self.active_character_label.setText("Active Character: None")

    def update_active_character_label(self):
        self.active_character_label.setText(f"Active Character: {self.character_file}")

    def load_character(self):
        options = QFileDialog.Options()
        character_data_dir = os.path.join(os.path.dirname(__file__), 'characterdata')
        file_name, _ = QFileDialog.getOpenFileName(self, "Select Character File", character_data_dir, "Character Files (*.chr);;All Files (*)", options=options)
        if file_name:
            self.character_file = os.path.splitext(os.path.basename(file_name))[0]
            character_path = os.path.join(os.path.dirname(file_name), self.character_file)
            if os.path.exists(f"{character_path}.chr"):
                with open(f"{character_path}.chr", "r") as file:
                    self.character_data = file.read()
                self.update_active_character_label()
            else:
                self.show_system_message("Character file not found.", "Error")
                self.active_character_label.setText("Active Character: None")

    def send_query(self):
        query = self.query_input.toPlainText()
        if not query or not self.character_file or not self.character_data:
            return

        self.response_display.setText("Thinking...")
        self.query_input.clear()

        # Create a new worker thread for the query
        self.worker = QueryWorker(query, self.character_file, self.character_data)
        self.worker.result_ready.connect(self.display_response_animated)  # Connect to the signal
        self.worker.error_occurred.connect(self.display_error)
        self.worker.start()

    def display_response_animated(self, response):
        self.animated_text = response
        self.current_text_index = 0
        self.response_display.clear()
        self.animation_timer.start(10)

        # Detect emotions from the response and display them in the emotions box
        emotions = detect_emotions([response])[0]
        emotions_text = "\n".join([f"{emotion}: {score:.2f}" for emotion, score in emotions.items()])
        self.emotions_display.setText(emotions_text)

        # Generate audio for the response using ElevenLabs
        self.generate_audio_for_response(response)

    def update_text_animation(self):
        if self.current_text_index < len(self.animated_text):
            self.response_display.insertPlainText(self.animated_text[self.current_text_index])
            self.current_text_index += 1
        else:
            self.animation_timer.stop()

    def display_error(self, error_message):
        self.response_display.setText(f"Error: {error_message}")

    def generate_audio_for_response(self, response):
        # Check if the ElevenLabs audio toggle in the menu is checked before generating the audio
        if self.audio_checkbox_action.isChecked():
            self.audio_worker = ElevenLabsAudioWorker(response)
            self.audio_worker.audio_ready.connect(self.play_audio_from_memory)
            self.audio_worker.error_occurred.connect(self.display_error)
            self.audio_worker.start()
        #else:
            #self.response_display.append("\n[ElevenLabs audio is disabled.]")

    def play_audio_from_memory(self, audio_bytes):
        # Play audio from in-memory bytes using pygame's mixer
        audio_stream = io.BytesIO(audio_bytes)
        mixer.music.load(audio_stream, 'mp3')
        mixer.music.play()

    def open_chat_history(self):
        if not self.character_file:
            self.show_system_message("No character loaded. Please load a character first.", "Warning")
            return
        chat_history_dialog = ChatHistoryDialog(self.character_file)
        chat_history_dialog.exec_()

    def toggle_fullscreen(self):
        if self.fullscreen:
            self.showNormal()
        else:
            self.showFullScreen()
        self.fullscreen = not self.fullscreen

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_F11:
            self.toggle_fullscreen()
        elif event.key() == Qt.Key_F4:
            self.toggle_speech_recognition()
        super().keyPressEvent(event)

    def toggle_speech_recognition(self):
        if self.speech_recognition_worker and self.speech_recognition_worker.isRunning():
            self.speech_recognition_worker.stop()
            self.update_speech_status(False)
        else:
            self.speech_recognition_worker = SpeechRecognitionWorker()
            self.speech_recognition_worker.recognized_text.connect(self.handle_speech_input)
            self.speech_recognition_worker.error_occurred.connect(self.display_error)
            self.speech_recognition_worker.recognition_started.connect(lambda: self.update_speech_status(True))
            self.speech_recognition_worker.recognition_stopped.connect(lambda: self.update_speech_status(False))
            self.speech_recognition_worker.start()

    def handle_speech_input(self, text):
        self.query_input.setPlainText(text)
        self.send_query()  # Automatically send the query after setting the recognized text

    def update_speech_status(self, is_on):
        if is_on:
            self.speech_status_label.setText("Speech Recognition (F4): ON")
            self.speech_status_label.setStyleSheet("color: green;")
        else:
            self.speech_status_label.setText("Speech Recognition (F4): OFF")
            self.speech_status_label.setStyleSheet("color: red;")

    def on_voice_model_changed(self, model_name):
        try:
            change_voice_model(model_name)
        except ValueError as e:
            self.show_system_message(str(e), "Error")

    def show_system_message(self, message, message_type="Information"):
        msg_box = QMessageBox(self)
        if message_type == "Error":
            msg_box.setIcon(QMessageBox.Critical)
            msg_box.setWindowTitle("Error")
        elif message_type == "Warning":
            msg_box.setIcon(QMessageBox.Warning)
            msg_box.setWindowTitle("Warning")
        else:
            msg_box.setIcon(QMessageBox.Information)
            msg_box.setWindowTitle("Information")
        msg_box.setText(message)
        msg_box.exec_()