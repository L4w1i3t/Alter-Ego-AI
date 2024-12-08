# construct.py

import os
import sqlite3
import json

from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QTextEdit,
    QLabel,
    QMessageBox,
    QSpacerItem,
    QSizePolicy,
    QDialog,
    QRadioButton,
    QButtonGroup,
    QListWidget,
    QLineEdit,
    QInputDialog,
    QScrollArea,
    QFrame,
)
from PyQt5.QtGui import QFont, QTextCursor, QGuiApplication, QPixmap
from PyQt5.QtCore import Qt, pyqtSignal, QDateTime

from model.elevenlabs_api import (
    add_voice_model,
    remove_voice_model,
)
from api_key_manager import APIKeyManager


class ChatHistoryDialog(QDialog):
    def __init__(self, character_file, model_name="gpt"):
        super().__init__()
        self.setWindowTitle("Chat History")
        self.setGeometry(100, 100, 1280, 720)
        self.setMinimumSize(800, 600)

        # Determine scaling factor based on screen resolution
        self.scaling_factor = self.get_scaling_factor()

        layout = QVBoxLayout()

        # Header Label
        header_layout = QHBoxLayout()
        header_label = QLabel(f"Chat History for {character_file}")
        header_font_size = int(16 * self.scaling_factor)
        header_label.setFont(QFont("Courier New", header_font_size, QFont.Bold))
        header_label.setStyleSheet("color: #FFFFFF;")
        header_layout.addWidget(header_label)
        header_layout.addSpacerItem(
            QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        )
        layout.addLayout(header_layout)

        # Chat History Display
        self.chat_history_display = QTextEdit()
        self.chat_history_display.setReadOnly(True)
        chat_display_font_size = int(12 * self.scaling_factor)
        self.chat_history_display.setFont(QFont("Courier New", chat_display_font_size))
        self.chat_history_display.setStyleSheet(
            """
            QTextEdit {
                background-color: #1E1E1E;
                color: #FFFFFF;
                border: 1px solid #00FF00;
                padding: 10px;
            }
            QTextEdit::-webkit-scrollbar {
                width: 12px;
            }
            QTextEdit::-webkit-scrollbar-track {
                background: #2E2E2E;
            }
            QTextEdit::-webkit-scrollbar-thumb {
                background-color: #00FF00;
                border-radius: 6px;
                border: 3px solid #2E2E2E;
            }
        """
        )
        self.chat_history_display.setWordWrapMode(True)  # Enable word wrap
        layout.addWidget(self.chat_history_display)

        # Footer
        footer_layout = QHBoxLayout()
        footer_layout.addSpacerItem(
            QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        )

        # Close Button
        close_button = QPushButton("Close")
        close_button_font_size = int(12 * self.scaling_factor)
        close_button.setFont(QFont("Courier New", close_button_font_size, QFont.Bold))
        close_button.setFixedSize(
            int(100 * self.scaling_factor), int(40 * self.scaling_factor)
        )
        close_button.setStyleSheet(
            """
            QPushButton {
                background-color: #00FF00;
                color: #000000;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #00CC00;
            }
        """
        )
        close_button.clicked.connect(self.accept)
        footer_layout.addWidget(close_button)

        layout.addLayout(footer_layout)

        self.setLayout(layout)
        self.load_character_memory(character_file, model_name)
        self.setStyleSheet(
            """
            QDialog {
                background-color: #121212;
            }
        """
        )

    def get_scaling_factor(self):
        screen = QGuiApplication.primaryScreen()
        size = screen.size()
        width = size.width()
        height = size.height()
        resolution = width * height

        if resolution <= 1920 * 1080:
            return 1.0  # 1080p
        elif resolution <= 2560 * 1440:
            return 1.25  # 1440p
        else:
            return 1.5  # 4K and above

    def load_character_memory(self, character_file, model_name="gpt"):
        # Define the memory database path based on the model
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        MEMORY_DB_DIR = os.path.join(BASE_DIR, "../persistent/memory_databases")
        db_path = os.path.join(
            MEMORY_DB_DIR, f"{character_file}_{model_name}_memory.db"
        )

        if os.path.exists(db_path):
            try:
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT query, response, id FROM memory ORDER BY id ASC")
                all_entries = cursor.fetchall()
                conn.close()

                if all_entries:
                    for entry_query, entry_response, entry_id in all_entries:
                        self.append_message("User", entry_query)
                        self.append_message("Assistant", entry_response)
                else:
                    self.append_message(
                        "System", "No interactions found for this character."
                    )
            except Exception as e:
                self.append_message("System", f"Error loading chat history: {str(e)}")
        else:
            self.append_message(
                "System", "No memory database found for this character."
            )

    def append_message(self, sender, message):
        # Define colors for different senders
        sender_colors = {
            "User": "#00FF00",
            "Assistant": "#1E90FF",
            "System": "#FF4500",
        }

        # Define font weight based on sender
        font_weights = {"User": "bold", "Assistant": "bold", "System": "normal"}

        # Define background colors for different senders
        sender_bg_colors = {
            "User": "#2E2E2E",
            "Assistant": "#1A1A1A",
            "System": "#3C3C3C",
        }

        # Get current timestamp
        timestamp = QDateTime.currentDateTime().toString("yyyy-MM-dd hh:mm:ss")

        # Determine font size based on scaling factor
        message_font_size = int(14 * self.scaling_factor)

        # Create HTML formatted string with bubble effect
        html_message = f"""
        <div style="
            background-color:{sender_bg_colors.get(sender, '#1E1E1E')};
            padding: 10px;
            border-radius: 10px;
            margin-bottom: 10px;
        ">
            <p style="
                color:{sender_colors.get(sender, '#FFFFFF')};
                font-weight:{font_weights.get(sender, 'normal')};
                margin: 0;
                font-size: {message_font_size}px;
            ">
                [{timestamp}] {sender}: {message}
            </p>
        </div>
        """

        # Insert HTML
        self.chat_history_display.moveCursor(QTextCursor.End)
        self.chat_history_display.insertHtml(html_message)
        self.chat_history_display.insertHtml("<br>")  # Add space between messages

        # Auto-scroll to the end
        self.chat_history_display.moveCursor(QTextCursor.End)


class SoftwareDetailsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Software Details")
        self.setGeometry(150, 150, 800, 800)
        self.setMinimumSize(600, 400)

        # Main layout
        main_layout = QVBoxLayout()

        # Header Section: Software Name and Developer
        header_layout = QVBoxLayout()

        # Software Name
        software_name_label = QLabel("Software: ALTER EGO")
        software_name_label.setFont(QFont("Courier New", 16, QFont.Bold))
        software_name_label.setStyleSheet("color: #00FF00;")  # Green color for titles
        header_layout.addWidget(software_name_label)

        # Developer
        developer_label = QLabel("Developed By: L4w1i3t")
        developer_label.setFont(QFont("Courier New", 14))
        developer_label.setStyleSheet("color: #FFFFFF;")  # White color for content
        header_layout.addWidget(developer_label)

        # Add some spacing after header
        header_layout.addSpacerItem(
            QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Fixed)
        )

        main_layout.addLayout(header_layout)

        # Scroll area to handle long content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)

        # Content widget inside the scroll area
        content_widget = QWidget()
        content_layout = QVBoxLayout()

        # Define sections with titles and content
        sections = [
            ("Text Generation", "OpenAI GPT-4o or Ollama"),
            ("Summarization Model", "OpenAI GPT-4o"),
            ("Embedding", "text-embedding-ada-002"),
            ("Voice Generation", "ElevenLabs (eleven_multilingual_v2)"),
            ("Speech Recognition", "OpenAI Whisper"),
            ("Emotion Detection", "RoBERTa-based (SamLowe-roberta-base-go_emotions)"),
            ("License", "MIT"),
        ]

        for title, content in sections:
            # Title Label
            title_label = QLabel(title)
            title_label.setFont(QFont("Courier New", 14, QFont.Bold))
            title_label.setStyleSheet("color: #00FF00;")  # Green color for titles
            content_layout.addWidget(title_label)

            # Content Label
            content_label = QLabel(content)
            content_label.setFont(QFont("Courier New", 12))
            content_label.setStyleSheet("color: #FFFFFF;")  # White color for content
            content_label.setWordWrap(True)
            content_label.setTextFormat(Qt.RichText)  # Enable HTML formatting
            content_layout.addWidget(content_label)

            # Spacer between sections
            spacer = QSpacerItem(20, 10, QSizePolicy.Minimum, QSizePolicy.Fixed)
            content_layout.addSpacerItem(spacer)

        # Add horizontal line before footer
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet("color: #00FF00;")  # Green color for separator
        content_layout.addWidget(separator)

        # Add "All rights reserved." at the bottom
        footer_label = QLabel("All rights reserved.")
        footer_label.setFont(QFont("Courier New", 12, QFont.Bold))
        footer_label.setStyleSheet("color: #FFFFFF;")  # White color for footer
        footer_label.setAlignment(Qt.AlignCenter)
        content_layout.addWidget(footer_label)

        # Set layout to content widget
        content_widget.setLayout(content_layout)
        scroll.setWidget(content_widget)
        main_layout.addWidget(scroll)

        # Close button layout
        button_layout = QHBoxLayout()
        button_layout.addSpacerItem(
            QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        )
        close_button = QPushButton("Close")
        close_button.setFixedSize(100, 40)
        close_button.setFont(QFont("Courier New", 12, QFont.Bold))
        close_button.setStyleSheet(
            """
            QPushButton {
                background-color: #00FF00;
                color: #000000;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #00CC00;
            }
        """
        )
        close_button.clicked.connect(self.accept)
        button_layout.addWidget(close_button)
        main_layout.addLayout(button_layout)

        self.setLayout(main_layout)
        self.setStyleSheet(
            """
            QDialog {
                background-color: #121212;
            }
        """
        )


class APIKeyManagerDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("API Key Settings")
        self.setFixedSize(500, 300)
        self.api_manager = APIKeyManager()
        layout = QVBoxLayout()

        # Define the services and their corresponding environment variable keys
        self.services = {"OpenAI": "openai", "ElevenLabs": "elevenlabs"}

        self.service_widgets = {}

        for service_name, service_key in self.services.items():
            service_layout = QHBoxLayout()
            label = QLabel(f"{service_name} API Key:")
            key = self.api_manager.get_api_key(service_key) or ""
            key_display = QLineEdit(key)
            key_display.setEchoMode(QLineEdit.Password)
            key_display.setReadOnly(True)
            edit_button = QPushButton("Edit")
            remove_button = QPushButton("Remove")

            # Connect buttons with corresponding methods
            edit_button.clicked.connect(lambda checked, s=service_key: self.edit_key(s))
            remove_button.clicked.connect(
                lambda checked, s=service_key: self.remove_key(s)
            )

            service_layout.addWidget(label)
            service_layout.addWidget(key_display)
            service_layout.addWidget(edit_button)
            service_layout.addWidget(remove_button)
            layout.addLayout(service_layout)

            self.service_widgets[service_key] = key_display

        # Add Close button
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)
        layout.addWidget(close_button, alignment=Qt.AlignRight)

        self.setLayout(layout)

    def edit_key(self, service):
        new_key, ok = QInputDialog.getText(
            self, f"Edit {service.capitalize()} API Key", "Enter new API key:"
        )
        if ok and new_key:
            success = self.api_manager.update_api_key(service, new_key)
            if success:
                self.service_widgets[service].setText(new_key)
                QMessageBox.information(
                    self,
                    "Success",
                    f"{service.capitalize()} API key updated successfully.",
                )
            else:
                QMessageBox.warning(
                    self, "Error", f"Failed to update {service.capitalize()} API key."
                )

    def remove_key(self, service):
        confirm = QMessageBox.question(
            self,
            "Confirm Remove",
            f"Are you sure you want to remove the {service.capitalize()} API key?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if confirm == QMessageBox.Yes:
            success = self.api_manager.remove_api_key(service)
            if success:
                self.service_widgets[service].setText("")
                QMessageBox.information(
                    self,
                    "Success",
                    f"{service.capitalize()} API key removed successfully.",
                )
            else:
                QMessageBox.warning(
                    self, "Error", f"Failed to remove {service.capitalize()} API key."
                )


class QueryTextEdit(QTextEdit):
    enterPressed = pyqtSignal()  # Custom signal for Enter key

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Return and not event.modifiers():
            # Enter without Shift - send query
            self.enterPressed.emit()
        elif event.key() == Qt.Key_Return and event.modifiers() & Qt.ShiftModifier:
            # Shift+Enter - insert newline
            super().keyPressEvent(event)
        else:
            # Handle all other keys normally
            super().keyPressEvent(event)


class ModelSelectionDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Text Generation Model")
        self.setFixedSize(500, 200)
        layout = QVBoxLayout()

        label = QLabel("Choose a Text Generation Model:")
        label.setFont(QFont("Courier New", 12))
        layout.addWidget(label)

        # Radio buttons for selection
        self.ollama_radio = QRadioButton("Ollama")
        self.openai_radio = QRadioButton("OpenAI API")
        self.openai_radio.setFont(QFont("Courier New", 16))
        self.ollama_radio.setFont(QFont("Courier New", 16))
        self.ollama_radio.setChecked(True)  # Default selection

        # Group the radio buttons
        self.button_group = QButtonGroup()
        self.button_group.addButton(self.openai_radio)
        self.button_group.addButton(self.ollama_radio)

        layout.addWidget(self.ollama_radio)
        layout.addWidget(self.openai_radio)

        # OK and Cancel buttons
        button_layout = QHBoxLayout()
        self.ok_button = QPushButton("OK")
        self.ok_button.clicked.connect(self.accept)
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_button)

        layout.addLayout(button_layout)
        self.setLayout(layout)

    def get_selection(self):
        if self.openai_radio.isChecked():
            return "openai"
        elif self.ollama_radio.isChecked():
            return "ollama"
        else:
            return None


class CharacterManagerDialog(QDialog):
    def __init__(self, parent=None, character_manager=None):
        super().__init__(parent)
        self.setWindowTitle("Manage Characters")
        self.setFixedSize(600, 400)
        self.character_manager = character_manager

        # Main layout
        main_layout = QVBoxLayout()

        # Character List
        self.character_list = QListWidget()
        self.load_characters()
        main_layout.addWidget(self.character_list)

        # Buttons Layout
        buttons_layout = QHBoxLayout()

        self.add_button = QPushButton("Add")
        self.add_button.clicked.connect(self.add_character)
        buttons_layout.addWidget(self.add_button)

        self.edit_button = QPushButton("Edit")
        self.edit_button.clicked.connect(self.edit_character)
        buttons_layout.addWidget(self.edit_button)

        self.duplicate_button = QPushButton("Duplicate")
        self.duplicate_button.clicked.connect(self.duplicate_character)
        buttons_layout.addWidget(self.duplicate_button)

        self.delete_button = QPushButton("Delete")
        self.delete_button.clicked.connect(self.delete_character)
        buttons_layout.addWidget(self.delete_button)

        main_layout.addLayout(buttons_layout)

        # Close Button
        close_button_layout = QHBoxLayout()
        close_button_layout.addStretch()
        self.close_button = QPushButton("Close")
        self.close_button.clicked.connect(self.accept)
        close_button_layout.addWidget(self.close_button)
        main_layout.addLayout(close_button_layout)

        self.setLayout(main_layout)

    def load_characters(self):
        """Load characters into the list widget."""
        self.character_list.clear()
        characters = self.character_manager.list_characters()
        self.character_list.addItems(characters)

    def add_character(self):
        """Add a new character."""
        name, ok = QInputDialog.getText(self, "Add Character", "Enter character name:")
        if ok and name:
            if self.character_manager.character_exists(name):
                QMessageBox.warning(
                    self, "Error", f"Character '{name}' already exists."
                )
                return
            content, ok = QInputDialog.getMultiLineText(
                self, "Add Character", "Enter character content:"
            )
            if ok:
                try:
                    self.character_manager.add_character(name, content)
                    self.load_characters()
                    QMessageBox.information(
                        self, "Success", f"Character '{name}' added successfully."
                    )
                except Exception as e:
                    QMessageBox.critical(self, "Error", str(e))

    def edit_character(self):
        """Edit the selected character."""
        selected_item = self.character_list.currentItem()
        if not selected_item:
            QMessageBox.warning(
                self, "No Selection", "Please select a character to edit."
            )
            return
        name = selected_item.text()
        character_path = self.character_manager.get_character_path(name)
        try:
            with open(character_path, "r", encoding="utf-8") as file:
                content = file.read()
        except Exception as e:
            QMessageBox.critical(
                self, "Error", f"Failed to read character file: {str(e)}"
            )
            return

        # Open a dialog to edit content
        dialog = EditCharacterDialog(self, name, content)
        if dialog.exec_() == QDialog.Accepted:
            new_content = dialog.get_content()
            try:
                self.character_manager.edit_character(name, new_content)
                self.load_characters()
                QMessageBox.information(
                    self, "Success", f"Character '{name}' edited successfully."
                )
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    def duplicate_character(self):
        """Duplicate the selected character."""
        selected_item = self.character_list.currentItem()
        if not selected_item:
            QMessageBox.warning(
                self, "No Selection", "Please select a character to duplicate."
            )
            return
        original_name = selected_item.text()
        new_name, ok = QInputDialog.getText(
            self, "Duplicate Character", "Enter new character name:"
        )
        if ok and new_name:
            if self.character_manager.character_exists(new_name):
                QMessageBox.warning(
                    self, "Error", f"Character '{new_name}' already exists."
                )
                return
            try:
                self.character_manager.duplicate_character(original_name, new_name)
                self.load_characters()
                QMessageBox.information(
                    self,
                    "Success",
                    f"Character '{original_name}' duplicated as '{new_name}' successfully.",
                )
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    def delete_character(self):
        """Delete the selected character."""
        selected_item = self.character_list.currentItem()
        if not selected_item:
            QMessageBox.warning(
                self, "No Selection", "Please select a character to delete."
            )
            return
        name = selected_item.text()
        confirm = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete character '{name}'?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if confirm == QMessageBox.Yes:
            try:
                self.character_manager.delete_character(name)
                self.load_characters()
                QMessageBox.information(
                    self, "Success", f"Character '{name}' deleted successfully."
                )
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))


class CharacterLoadDialog(QDialog):
    def __init__(self, character_manager, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Load Character")
        self.setFixedSize(600, 400)

        self.character_manager = character_manager

        layout = QVBoxLayout()

        label = QLabel("Select a character to load:")
        layout.addWidget(label)

        # Character List
        self.character_list = QListWidget()
        self.load_characters()
        layout.addWidget(self.character_list)

        # Buttons
        button_layout = QHBoxLayout()
        load_button = QPushButton("Load")
        load_button.clicked.connect(self.load_character)
        button_layout.addWidget(load_button)

        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)

        layout.addLayout(button_layout)

        self.setLayout(layout)

    def load_characters(self):
        """Load characters into the list widget."""
        characters = self.character_manager.list_characters()
        self.character_list.addItems(characters)

    def load_character(self):
        """Load the selected character."""
        selected_item = self.character_list.currentItem()
        if selected_item:
            self.accept()  # Close the dialog and return success
        else:
            QMessageBox.warning(
                self, "No Selection", "Please select a character to load."
            )


class EditCharacterDialog(QDialog):
    def __init__(self, parent=None, character_name="", content=""):
        super().__init__(parent)
        self.setWindowTitle(f"Edit Character: {character_name}")
        self.setFixedSize(500, 400)
        self.character_name = character_name

        # Main layout
        main_layout = QVBoxLayout()

        # Content TextEdit
        self.content_edit = QTextEdit()
        self.content_edit.setText(content)
        main_layout.addWidget(self.content_edit)

        # Buttons Layout
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()

        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self.accept)
        buttons_layout.addWidget(self.save_button)

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        buttons_layout.addWidget(self.cancel_button)

        main_layout.addLayout(buttons_layout)

        self.setLayout(main_layout)

    def get_content(self):
        return self.content_edit.toPlainText()


class VoiceModelManager(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Manage Voice Models")
        self.setGeometry(100, 100, 800, 600)
        self.models_file = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "persistent",
            "elevenlabs_models.json",
        )

        layout = QVBoxLayout()
        font = QFont()
        font.setPointSize(12)

        self.model_list = QListWidget()
        self.model_list.setFont(font)

        self.name_input = QLineEdit()
        self.name_input.setFont(font)
        self.id_input = QLineEdit()
        self.id_input.setFont(font)

        add_button = QPushButton("Add Model")
        add_button.setFont(font)
        remove_button = QPushButton("Remove Model")
        remove_button.setFont(font)

        # Create labels with the same font
        name_label = QLabel("Model Name:")
        name_label.setFont(font)
        id_label = QLabel("Model ID:")
        id_label.setFont(font)

        # Set up the layout
        layout.addWidget(self.model_list)

        input_layout = QHBoxLayout()
        input_layout.addWidget(name_label)
        input_layout.addWidget(self.name_input)
        input_layout.addWidget(id_label)
        input_layout.addWidget(self.id_input)
        layout.addLayout(input_layout)

        button_layout = QHBoxLayout()
        button_layout.addWidget(add_button)
        button_layout.addWidget(remove_button)
        layout.addLayout(button_layout)

        self.setLayout(layout)

        # Connect buttons to functions
        add_button.clicked.connect(self.add_model)
        remove_button.clicked.connect(self.remove_model)

        # Load existing models
        self.load_models()

    def load_models(self):
        try:
            with open(self.models_file, "r", encoding="utf-8-sig") as f:
                content = f.read().strip()
                if not content:
                    self.voice_models_data = {}
                    print(f"{self.models_file} is empty. No voice models loaded.")
                else:
                    self.voice_models_data = json.loads(content)
            self.model_list.clear()
            self.model_list.addItems(self.voice_models_data.keys())
        except FileNotFoundError:
            print(
                f"Could not find voice models file at: {self.models_file}. Initializing with no voice models."
            )
            self.voice_models_data = {}
            with open(self.models_file, "w", encoding="utf-8") as f:
                json.dump({}, f, indent=4)
        except json.JSONDecodeError as e:
            print(f"{self.models_file} is malformed: {str(e)}. Resetting to empty.")
            self.voice_models_data = {}
            with open(self.models_file, "w", encoding="utf-8") as f:
                json.dump({}, f, indent=4)
        except Exception as e:
            print(f"Error loading voice models: {str(e)}")
            self.voice_models_data = {}

    def add_model(self):
        name = self.name_input.text().strip()
        model_id = self.id_input.text().strip()
        if name and model_id:
            success = add_voice_model(
                name, model_id
            )  # Using function from elevenlabs_api.py
            if success:
                self.model_list.addItem(name)
                self.name_input.clear()
                self.id_input.clear()
                self.parent().load_voice_models()  # Notify parent to reload
                self.parent().show_system_message(
                    f"Voice model '{name}' added successfully.", "Information"
                )
            else:
                QMessageBox.warning(self, "Error", "Failed to add the voice model.")
        else:
            QMessageBox.warning(self, "Error", "Both name and ID must be provided.")

    def remove_model(self):
        current_item = self.model_list.currentItem()
        if current_item:
            name = current_item.text()
            success = remove_voice_model(name)  # Using function from elevenlabs_api.py
            if success:
                self.model_list.takeItem(self.model_list.row(current_item))
                self.parent().load_voice_models()  # Notify parent to reload
                self.parent().show_system_message(
                    f"Voice model '{name}' removed successfully.", "Information"
                )
            else:
                QMessageBox.warning(self, "Error", "Failed to remove the voice model.")

    def show_message(self, title, message):
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.setFont(QFont("Arial", 12))  # Set font for message box
        msg_box.exec_()


class AvatarWidget(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet(
            """
            QLabel {
                border: 2px solid #00FF00;
                background-color: black;
            }
        """
        )
        self.character_folder = None  # Store character-specific folder

    def set_character_folder(self, folder):
        """Set the folder for character-specific avatars."""
        self.character_folder = folder
        self.load_avatar(
            "neutral"
        )  # Load the neutral avatar for the character once the folder is set

    def load_avatar(self, emotion):
        """Load the avatar image based on the detected emotion, falling back to neutral if not found."""
        # Ensure that a character folder is set
        if self.character_folder is None:
            self.setText("Character folder not set.")
            return

        # Construct the path to the avatar image
        base_path = os.path.join(
            os.path.dirname(__file__), "avatar/sprites", self.character_folder
        )
        avatar_path = os.path.join(base_path, f"{emotion}.png")

        # If the emotion-specific avatar is not found, fallback to neutral for the character
        if not os.path.exists(avatar_path):
            avatar_path = os.path.join(base_path, "neutral.png")

        # Load the avatar image if it exists, otherwise display an error message
        if os.path.exists(avatar_path):
            pixmap = QPixmap(avatar_path)
            self.setPixmap(
                pixmap.scaled(self.width(), self.height(), Qt.KeepAspectRatio)
            )
        else:
            self.setText(f"Avatar for '{emotion}' not found in {self.character_folder}")

    def adjust_avatar_size(self, width, height):
        """Adjust avatar size based on the resolution of the application."""
        self.setFixedSize(width, height)
        if self.character_folder:
            self.load_avatar(
                "neutral"
            )  # Reload avatar only if the character folder is set
