# gui.py

import os
import sys

# Add the root to sys.path for module imports. Code breaks without this for some reason
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QTextEdit,
    QLabel,
    QMenuBar,
    QAction,
    QMainWindow,
    QMessageBox,
    QSpacerItem,
    QSizePolicy,
    QComboBox,
    QDialog,
    QCheckBox,
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QFont
import io
import logging
import warnings
import os
from PyQt5.QtCore import QTimer

warnings.simplefilter(action="ignore", category=FutureWarning)
warnings.simplefilter(
    action="ignore", category=UserWarning
)  # Pesky little Pydantic warning suppression
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "hide"
from pygame import mixer  # For playing audio
import datetime
import traceback

# Import necessary API stuff for the main class
from model.emotions import detect_emotions
from model.elevenlabs_api import (
    change_voice_model,
    reload_voice_models,
    get_available_voice_models,
)

# Import helper files
from workers import QueryWorker, SpeechRecognitionWorker, ElevenLabsAudioWorker
from construct import (
    ChatHistoryDialog,
    SoftwareDetailsDialog,
    APIKeyManagerDialog,
    QueryTextEdit,
    ModelSelectionDialog,
    CharacterManagerDialog,
    CharacterLoadDialog,
    VoiceModelManager,
    AvatarWidget,
)
from character_manager import CharacterManager
from model import textgen_llama

# Initialize pygame mixer for audio playback
mixer.init()


# Log crashes to a file
def ensure_crash_reports_dir():
    global crash_reports_dir
    
    # Get the absolute path of the root directory (two levels up from gui.py)
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    crash_reports_dir = os.path.join(root_dir, "persistent", "crash_reports")
    
    if not os.path.exists(crash_reports_dir):
        os.makedirs(crash_reports_dir)


def log_crash(exc_type, exc_value, exc_traceback):
    ensure_crash_reports_dir()

    # Create a timestamped file for the crash report
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    crash_file_path = os.path.join(crash_reports_dir, f"crash_report_{timestamp}.txt")

    # Write the crash details into the report
    with open(crash_file_path, "w") as f:
        f.write(f"Crash Report - {datetime.datetime.now()}\n")
        f.write("Type: {}\n".format(exc_type.__name__))
        f.write("Value: {}\n".format(exc_value))
        f.write("Traceback:\n")
        traceback.print_tb(exc_traceback, file=f)

    # Print the crash info to the console as well
    print(f"App crashed. Report saved to {crash_file_path}")


# Set up the custom exception hook to log crashes
sys.excepthook = log_crash


def open_voice_model_manager(self):
    dialog = VoiceModelManager(self)
    dialog.exec_()
    # After the dialog is closed, reload voice models and update the combo box
    self.load_voice_models()


# Main application window
###################################################################################################################################################################################
class AlterEgo(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ALTER EGO")
        self.setGeometry(100, 100, 1920, 1080)
        self.setMinimumSize(1280, 720)
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        self.layout = QVBoxLayout()

        # Initialize a list to keep track of child windows
        self.child_windows = []

        # Initialize model selection
        self.text_generation_model = None
        self.initialize_model_selection()

        # Initialize Character Manager
        self.character_manager = CharacterManager()

        # Character loading and active character display
        button_and_label_layout = QVBoxLayout()
        self.load_button = QPushButton("Load Character")
        self.load_button.setFixedSize(150, 50)
        self.load_button.setObjectName("loadButton")
        self.load_button.clicked.connect(self.load_character)
        button_and_label_layout.addWidget(self.load_button, alignment=Qt.AlignLeft)

        # Displays the active character being used
        self.active_character_label = QLabel(f"Active Character: Loading...", self)
        italic_font = QFont("Courier New", 16)
        italic_font.setItalic(True)
        self.active_character_label.setFont(italic_font)
        button_and_label_layout.addWidget(
            self.active_character_label, alignment=Qt.AlignLeft
        )
        self.layout.addLayout(button_and_label_layout)

        # Query input and buttons (Send Query)
        input_and_button_layout = QHBoxLayout()
        self.query_input = (
            QueryTextEdit()
        )  # Use custom QueryTextEdit instead of QTextEdit
        self.query_input.setFont(QFont("Courier New", 14))
        self.query_input.setPlaceholderText(
            "Type your query here... (Press Enter to send, Shift+Enter for new line)"
        )
        self.query_input.setFixedHeight(75)
        self.query_input.enterPressed.connect(self.send_query)  # Connect the signal
        input_and_button_layout.addWidget(self.query_input)

        # Send Query button
        self.send_button = QPushButton("Send Query")
        self.send_button.setFixedSize(150, 50)
        self.send_button.setObjectName("sendButton")
        self.send_button.clicked.connect(self.send_query)
        input_and_button_layout.addWidget(self.send_button)

        self.layout.addLayout(input_and_button_layout)

        # Response and Avatar Layout
        response_and_avatar_layout = QHBoxLayout()

        # Response display area
        self.response_label = QLabel("Response:")
        self.response_label.setFont(QFont("Courier New", 14))
        self.response_display = QTextEdit()
        self.response_display.setFont(QFont("Courier New", 14))
        self.response_display.setReadOnly(True)

        response_layout = QVBoxLayout()
        response_layout.addWidget(self.response_label)
        response_layout.addWidget(self.response_display)

        # Avatar display area
        self.avatar_widget = AvatarWidget()

        # Add both response and avatar to the layout
        response_and_avatar_layout.addLayout(response_layout)
        response_and_avatar_layout.addWidget(self.avatar_widget)

        self.layout.addLayout(response_and_avatar_layout)

        # Add emotions display box in the bottom left corner
        emotions_layout = QHBoxLayout()
        self.emotions_label = QLabel("Detected Emotions:")
        self.emotions_label.setFont(QFont("Courier New", 14))
        self.emotions_display = QTextEdit()
        self.emotions_display.setFont(QFont("Courier New", 14))
        self.emotions_display.setReadOnly(True)
        self.emotions_display.setFixedHeight(100)
        self.emotions_display.setFixedWidth(300)
        self.emotions_display.setObjectName("emotionsDisplay")

        emotions_layout.addWidget(self.emotions_label)
        emotions_layout.addWidget(self.emotions_display)
        emotions_layout.addSpacerItem(
            QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        )

        self.layout.addLayout(emotions_layout)

        # Speech Recognition status label
        self.speech_status_label = QLabel("Speech Recognition (F4): OFF")
        self.speech_status_label.setFont(QFont("Courier New", 14))
        self.speech_status_label.setStyleSheet("color: red;")  # Default to OFF
        self.layout.addWidget(self.speech_status_label)

        # Voice Model Selection (properly aligned on the left)
        voice_model_layout = QHBoxLayout()
        self.voice_model_label = QLabel("Voice Model:")
        self.voice_model_label.setFont(QFont("Courier New", 14))
        voice_model_layout.addWidget(self.voice_model_label)

        self.voice_model_combo = QComboBox()
        combo_font = QFont("Courier New", 14)
        self.voice_model_combo.setFont(combo_font)
        self.voice_model_combo.addItems(get_available_voice_models())
        self.voice_model_combo.currentTextChanged.connect(self.on_voice_model_changed)
        voice_model_layout.addWidget(self.voice_model_combo)

        self.manage_models_button = QPushButton("Manage Voice Models")
        self.manage_models_button.clicked.connect(self.open_voice_model_manager)
        voice_model_layout.addWidget(self.manage_models_button)

        # Add ElevenLabs Audio Toggle
        self.audio_checkbox = QCheckBox("Enable ElevenLabs Speech Audio")
        self.audio_checkbox.setFont(QFont("Courier New", 14))
        self.audio_checkbox.setChecked(False)  # Default OFF
        voice_model_layout.addWidget(self.audio_checkbox)

        voice_model_layout.addSpacerItem(
            QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        )

        self.layout.addLayout(voice_model_layout)

        central_widget.setLayout(self.layout)

        # Menu setup
        self.menu_bar = QMenuBar(self)
        self.setMenuBar(self.menu_bar)
        self.menu = self.menu_bar.addMenu("☰")

        # Add "New Conversation" to the menu
        self.add_new_conversation_menu()

        # Chat History
        self.chat_history_action = QAction("Chat History", self)
        self.chat_history_action.triggered.connect(self.open_chat_history)
        self.menu.addAction(self.chat_history_action)

        # Fullscreen
        self.fullscreen_action = QAction("Toggle Fullscreen", self)
        self.fullscreen_action.triggered.connect(self.toggle_fullscreen)
        self.menu.addAction(self.fullscreen_action)

        # Software Details
        self.software_details_action = QAction("Software Details", self)
        self.software_details_action.triggered.connect(self.open_software_details)
        self.menu.addAction(self.software_details_action)

        # API Key Settings
        self.api_settings_action = QAction("API Key Settings", self)
        self.api_settings_action.triggered.connect(self.open_api_key_settings)
        self.menu.addAction(self.api_settings_action)

        # Character Data Management
        self.manage_characters_action = QAction("Manage Characters", self)
        self.manage_characters_action.triggered.connect(self.open_character_manager)
        self.menu.addAction(self.manage_characters_action)

        self.character_file = None
        self.character_data = None
        self.animation_timer = QTimer(self)
        self.animation_timer.timeout.connect(self.update_text_animation)
        self.animated_text = ""
        self.current_text_index = 0
        self.fullscreen = False
        self.speech_recognition_worker = None

        # Adjust avatar size based on initial resolution
        self.adjust_avatar_size()

        # Stylesheet for UI elements
        self.setStyleSheet(
            """
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
                font-size: 15px;
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
            """
        )

        # Attempt to load DEFAULT.chr
        self.load_default_character()

    def initialize_model_selection(self):
        dialog = ModelSelectionDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            self.text_generation_model = dialog.get_selection()
            print(f"Selected text generation model: {self.text_generation_model}")
            if self.text_generation_model == "ollama":
                # Start Ollama server
                textgen_llama.start_ollama_server()
        else:
            # User canceled the selection, exit the application
            sys.exit()

    def load_default_character(self):
        default_character_file = "DEFAULT"
        character_path = os.path.join(
            os.path.dirname(__file__),
            "../persistent/characterdata",
            f"{default_character_file}.chr",
        )
        if os.path.exists(character_path):
            with open(character_path, "r") as file:
                self.character_file = default_character_file
                self.character_data = file.read()
                self.update_active_character_label()

                # Derive avatar folder from character file name
                avatar_folder = self.derive_avatar_folder(self.character_file)
                print(
                    f"Loading avatar folder: {avatar_folder}"
                )  # Debugging: Show the extracted folder name
                self.avatar_widget.set_character_folder(avatar_folder)

                # Enable query inputs and speech recognition
                self.enable_query_features()
        else:
            self.character_file = None
            self.character_data = None
            self.active_character_label.setText("Active Character: None")
            self.disable_query_features()
            self.show_system_message(
                "DEFAULT character not found. Please load a character to begin.",
                "Warning",
            )

    def update_active_character_label(self):
        self.active_character_label.setText(f"Active Character: {self.character_file}")

    def load_character(self):
        # Open the Character Load Dialog to select a character
        character_load_dialog = CharacterLoadDialog(self.character_manager, self)

        if character_load_dialog.exec_() == QDialog.Accepted:
            # Get the selected character name from the dialog
            selected_character_name = (
                character_load_dialog.character_list.currentItem().text()
            )

            # Load the character data
            character_path = self.character_manager.get_character_path(
                selected_character_name
            )
            try:
                with open(character_path, "r", encoding="utf-8") as file:
                    self.character_file = selected_character_name
                    self.character_data = file.read()

                    # Check if the character data is empty
                    if not self.character_data.strip():
                        self.show_system_message(
                            "Warning: The character file is empty. The program may not work as intended.",
                            "Warning",
                        )

                    self.update_active_character_label()  # Update the UI to show the active character

                    # Derive avatar folder from character file name
                    avatar_folder = self.derive_avatar_folder(self.character_file)
                    print(
                        f"Loading avatar folder: {avatar_folder}"
                    )  # Debugging: Show the extracted folder name
                    self.avatar_widget.set_character_folder(avatar_folder)

                    # Enable query inputs and speech recognition
                    self.enable_query_features()
            except Exception as e:
                self.show_system_message(
                    f"Failed to load character '{selected_character_name}': {str(e)}",
                    "Error",
                )

    def derive_avatar_folder(self, character_file_name):
        """Automatically derive the avatar folder from the character's file name."""
        # Construct the path to the character's avatar folder
        avatar_folder_path = os.path.join(
            os.path.dirname(__file__), "avatar", "sprites", character_file_name
        )

        # Debugging: Print the path being checked
        print(f"Checking if avatar folder exists: {avatar_folder_path}")

        # Check if the folder exists
        if os.path.exists(avatar_folder_path):
            print(f"Character-specific folder found: {character_file_name}")
            return character_file_name  # Return the character's folder if it exists
        else:
            print("Character-specific folder not found, defaulting to 'DEFAULT'")
            return "DEFAULT"  # Fallback to DEFAULT if the folder doesn't exist

    def send_query(self):
        query = self.query_input.toPlainText()
        if not query or not self.character_file or not self.character_data:
            return

        self.response_display.setText("Thinking...")
        self.query_input.clear()

        # Create a new worker thread for the query
        self.worker = QueryWorker(
            query, self.character_file, self.character_data, self.text_generation_model
        )
        self.worker.result_ready.connect(self.display_response_animated)
        self.worker.error_occurred.connect(self.display_error)
        self.worker.start()

    def display_response_animated(self, response):
        self.animated_text = response
        self.current_text_index = 0
        self.response_display.clear()
        self.animation_timer.start(10)

        # Detect emotions from the response
        emotions = detect_emotions([response])[0]

        # Find the highest detected emotion
        highest_emotion = max(emotions, key=emotions.get)

        # Update the avatar based on the highest emotion
        self.avatar_widget.load_avatar(highest_emotion)

        # Display the detected emotions in the emotions display box
        emotions_text = "\n".join(
            [f"{emotion}: {score:.2f}" for emotion, score in emotions.items()]
        )
        self.emotions_display.setText(emotions_text)

        # Generate audio for the response (if applicable)
        self.generate_audio_for_response(response)

    def update_text_animation(self):
        if self.current_text_index < len(self.animated_text):
            self.response_display.insertPlainText(
                self.animated_text[self.current_text_index]
            )
            self.current_text_index += 1
        else:
            self.animation_timer.stop()

    def display_error(self, error_message):
        self.response_display.setText(f"Error: {error_message}")

    def generate_audio_for_response(self, response):
        # Check if the ElevenLabs audio toggle is checked before generating the audio
        if self.audio_checkbox.isChecked():
            self.audio_worker = ElevenLabsAudioWorker(response)
            self.audio_worker.audio_ready.connect(self.play_audio_from_memory)
            self.audio_worker.error_occurred.connect(self.display_error)
            self.audio_worker.start()
        # else:
        #     self.response_display.append("\n[ElevenLabs audio is disabled.]")

    def play_audio_from_memory(self, audio_bytes):
        logging.info(f"Attempting to play audio. Size: {len(audio_bytes)} bytes")
        try:
            audio_stream = io.BytesIO(audio_bytes)
            mixer.music.load(audio_stream, "mp3")
            mixer.music.play()
            logging.info("Audio playback started")
        except Exception as e:
            logging.error(f"Error playing audio: {str(e)}")
            self.display_error(f"Error playing audio: {str(e)}")

    def check_playback_finished(self, temp_audio_path, timer):
        if not mixer.music.get_busy():
            timer.stop()
            try:
                os.remove(temp_audio_path)
                logging.info(f"Deleted temporary audio file: {temp_audio_path}")
            except Exception as e:
                logging.error(f"Error deleting temporary audio file: {str(e)}")
                self.display_error(f"Error deleting temporary audio file: {str(e)}")

    def open_chat_history(self):
        if not self.character_file:
            self.show_system_message(
                "No character loaded. Please load a character first.", "Warning"
            )
            return
        chat_history_dialog = ChatHistoryDialog(
            self.character_file, self.text_generation_model
        )
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
        if (
            self.speech_recognition_worker
            and self.speech_recognition_worker.isRunning()
        ):
            self.speech_recognition_worker.stop()
            self.speech_recognition_worker.finished.connect(self.cleanup_speech_worker)
        else:
            self.speech_recognition_worker = SpeechRecognitionWorker()
            self.speech_recognition_worker.recognized_text.connect(
                self.handle_speech_input
            )
            self.speech_recognition_worker.error_occurred.connect(self.display_error)
            self.speech_recognition_worker.recognition_started.connect(
                lambda: self.update_speech_status(True)
            )
            self.speech_recognition_worker.recognition_stopped.connect(
                lambda: self.update_speech_status(False)
            )
            self.speech_recognition_worker.finished.connect(self.cleanup_speech_worker)
            self.speech_recognition_worker.start()

    def cleanup_speech_worker(self):
        if self.speech_recognition_worker:
            self.speech_recognition_worker.deleteLater()
            self.speech_recognition_worker = None

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

    def adjust_avatar_size(self):
        window_size = self.size()  # Get the application window size
        if 1080 <= window_size.height() <= 1599:  # From 1080p to 4k
            self.avatar_widget.adjust_avatar_size(650, 650)
        elif 1600 <= window_size.height() <= 2160:  # From 2k to 4k
            self.avatar_widget.adjust_avatar_size(1000, 1000)
        else:
            self.avatar_widget.adjust_avatar_size(400, 400)

    def resizeEvent(self, event):
        self.adjust_avatar_size()
        super().resizeEvent(event)

    # Function to show software details
    def open_software_details(self):
        dialog = SoftwareDetailsDialog(self)
        dialog.exec_()

    # Override closeEvent to ensure Ollama server is closed if running
    def closeEvent(self, event):
        if self.text_generation_model == "ollama":
            try:
                textgen_llama.stop_ollama_server()
            except Exception as e:
                print(f"Error stopping Ollama server: {e}")
        # Close all child windows
        for window in self.child_windows[:]:
            window.close()
        event.accept()

    def enable_query_features(self):
        """Enable query input and speech recognition features."""
        self.query_input.setEnabled(True)
        self.send_button.setEnabled(True)
        self.speech_status_label.setEnabled(True)
        self.menu.setEnabled(True)
        self.voice_model_combo.setEnabled(True)
        # Display a message to the user. Commented out right now because it happens upon EVERY character load
        # self.show_system_message("Character loaded successfully. You can now enter queries and enable speech recognition.", "Information")

    def disable_query_features(self):
        """Disable query input and speech recognition features."""
        self.query_input.setEnabled(False)
        self.send_button.setEnabled(False)
        self.speech_status_label.setEnabled(False)
        self.menu.setEnabled(False)
        self.voice_model_combo.setEnabled(False)

        # Disable speech recognition if it's running
        if (
            self.speech_recognition_worker
            and self.speech_recognition_worker.isRunning()
        ):
            self.speech_recognition_worker.stop()
            self.speech_recognition_worker.finished.connect(self.cleanup_speech_worker)

    def open_voice_model_manager(self):
        dialog = VoiceModelManager(self)
        dialog.exec_()
        # After the dialog is closed, reload voice models and update the combo box
        self.load_voice_models()

    # Load voice models
    def load_voice_models(self):
        try:
            reload_voice_models()  # Reload the latest models
            self.voice_model_combo.clear()
            models = get_available_voice_models()
            self.voice_model_combo.addItems(models)
            self.update_elevenlabs_availability()
            logging.info("Voice models loaded into GUI successfully.")

            if not models:
                self.show_system_message(
                    "No voice models available. ElevenLabs services will be unavailable.",
                    "Warning",
                )
        except Exception as e:
            logging.error(f"Error loading voice models into GUI: {str(e)}")
            self.voice_model_combo.clear()
            self.update_elevenlabs_availability()
            self.show_system_message("Failed to load voice models.", "Error")

    # Update ElevenLabs availability
    def update_elevenlabs_availability(self):
        available_models = get_available_voice_models()
        if not available_models:
            self.audio_checkbox.setChecked(False)
            self.audio_checkbox.setEnabled(False)
            self.voice_model_combo.setEnabled(False)
            logging.info("No voice models available. Audio features disabled.")
        else:
            self.audio_checkbox.setEnabled(True)
            self.voice_model_combo.setEnabled(True)
            logging.info("Voice models are available. Audio features enabled.")

    def open_api_key_settings(self):
        dialog = APIKeyManagerDialog(self)
        dialog.exec_()

    def open_character_manager(self):
        dialog = CharacterManagerDialog(self, self.character_manager)
        dialog.exec_()

    def add_new_conversation_menu(self):
        # Create a new QAction for opening a new conversation
        new_conv_action = QAction("Create New Window", self)
        new_conv_action.setShortcut("Ctrl+N")
        new_conv_action.triggered.connect(self.open_new_conversation)

        # Insert the new action at the top of the menu for better visibility
        # Check if there are existing actions to insert before
        if self.menu.actions():
            self.menu.insertAction(self.menu.actions()[0], new_conv_action)
        else:
            self.menu.addAction(new_conv_action)

    def open_new_conversation(self):
        # Create a new instance of AlterEgo
        new_window = AlterEgo()
        new_window.setWindowTitle(f"ALTER EGO - Child Instance")

        # Append the new window to the child_windows list to keep a reference
        self.child_windows.append(new_window)

        # Show the new window
        new_window.show()

        # Connect the close event to remove the window from the list when closed
        new_window.destroyed.connect(lambda: self.child_windows.remove(new_window))
