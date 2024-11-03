# construct.py

import os
import sqlite3
from PyQt5.QtWidgets import (
    QVBoxLayout, QTextEdit, QDialog, QLabel, QHBoxLayout, QSpacerItem,
    QSizePolicy, QPushButton, QWidget, QScrollArea, QFrame
)
from PyQt5.QtGui import QFont, QTextCursor, QColor, QGuiApplication
from PyQt5.QtCore import Qt, QDateTime

class ChatHistoryDialog(QDialog):
    def __init__(self, character_file, model_name='gpt'):
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
        header_label.setFont(QFont('Courier New', header_font_size, QFont.Bold))
        header_label.setStyleSheet("color: #FFFFFF;")  # Set header text color to white
        header_layout.addWidget(header_label)
        header_layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))
        layout.addLayout(header_layout)
        
        # Chat History Display
        self.chat_history_display = QTextEdit()
        self.chat_history_display.setReadOnly(True)
        chat_display_font_size = int(12 * self.scaling_factor)
        self.chat_history_display.setFont(QFont('Courier New', chat_display_font_size))
        self.chat_history_display.setStyleSheet("""
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
        """)
        self.chat_history_display.setWordWrapMode(True)  # Enable word wrap
        layout.addWidget(self.chat_history_display)
        
        # Footer (Optional: Could include buttons or additional info)
        footer_layout = QHBoxLayout()
        footer_layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))
        
        # Close Button
        close_button = QPushButton("Close")
        close_button_font_size = int(12 * self.scaling_factor)
        close_button.setFont(QFont('Courier New', close_button_font_size, QFont.Bold))
        close_button.setFixedSize(int(100 * self.scaling_factor), int(40 * self.scaling_factor))
        close_button.setStyleSheet("""
            QPushButton {
                background-color: #00FF00;
                color: #000000;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #00CC00;
            }
        """)
        close_button.clicked.connect(self.accept)
        footer_layout.addWidget(close_button)
        
        layout.addLayout(footer_layout)
        
        self.setLayout(layout)
        self.load_character_memory(character_file, model_name)
        self.setStyleSheet("""
            QDialog {
                background-color: #121212;
            }
        """)

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

    def load_character_memory(self, character_file, model_name='gpt'):
        # Define the memory database path based on the model
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        MEMORY_DB_DIR = os.path.join(BASE_DIR, '../memory_databases')
        db_path = os.path.join(MEMORY_DB_DIR, f"{character_file}_{model_name}_memory.db")

        if os.path.exists(db_path):
            try:
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                cursor.execute('SELECT query, response, id FROM memory ORDER BY id ASC')
                all_entries = cursor.fetchall()
                conn.close()

                if all_entries:
                    for entry_query, entry_response, entry_id in all_entries:
                        self.append_message("User", entry_query)
                        self.append_message("Assistant", entry_response)
                else:
                    self.append_message("System", "No interactions found for this character.")
            except Exception as e:
                self.append_message("System", f"Error loading chat history: {str(e)}")
        else:
            self.append_message("System", "No memory database found for this character.")

    def append_message(self, sender, message):
        """
        Appends a message to the chat history display with HTML formatting.
        :param sender: 'User' or 'Assistant' or 'System'
        :param message: The message content
        """
        # Define colors for different senders
        sender_colors = {
            "User": "#00FF00",        # Green
            "Assistant": "#1E90FF",   # Dodger Blue
            "System": "#FF4500"       # Orange Red
        }

        # Define font weight based on sender
        font_weights = {
            "User": "bold",
            "Assistant": "bold",
            "System": "normal"
        }

        # Define background colors for different senders
        sender_bg_colors = {
            "User": "#2E2E2E",        # Dark Grey for User
            "Assistant": "#1A1A1A",   # Slightly Darker Grey for Assistant
            "System": "#3C3C3C"        # Different Shade for System
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
        software_name_label.setFont(QFont('Courier New', 16, QFont.Bold))
        software_name_label.setStyleSheet("color: #00FF00;")  # Green color for titles
        header_layout.addWidget(software_name_label)
        
        # Developer
        developer_label = QLabel("Developed By: L4w1i3t")
        developer_label.setFont(QFont('Courier New', 14))
        developer_label.setStyleSheet("color: #FFFFFF;")  # White color for content
        header_layout.addWidget(developer_label)
        
        # Add some spacing after header
        header_layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Fixed))
        
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
            ("License", "MIT")
        ]
        
        for title, content in sections:
            # Title Label
            title_label = QLabel(title)
            title_label.setFont(QFont('Courier New', 14, QFont.Bold))
            title_label.setStyleSheet("color: #00FF00;")  # Green color for titles
            content_layout.addWidget(title_label)
            
            # Content Label
            content_label = QLabel(content)
            content_label.setFont(QFont('Courier New', 12))
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
        footer_label.setFont(QFont('Courier New', 12, QFont.Bold))
        footer_label.setStyleSheet("color: #FFFFFF;")  # White color for footer
        footer_label.setAlignment(Qt.AlignCenter)
        content_layout.addWidget(footer_label)
        
        # Set layout to content widget
        content_widget.setLayout(content_layout)
        scroll.setWidget(content_widget)
        main_layout.addWidget(scroll)
        
        # Close button layout
        button_layout = QHBoxLayout()
        button_layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))
        close_button = QPushButton("Close")
        close_button.setFixedSize(100, 40)
        close_button.setFont(QFont('Courier New', 12, QFont.Bold))
        close_button.setStyleSheet("""
            QPushButton {
                background-color: #00FF00;
                color: #000000;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #00CC00;
            }
        """)
        close_button.clicked.connect(self.accept)
        button_layout.addWidget(close_button)
        main_layout.addLayout(button_layout)
        
        self.setLayout(main_layout)
        self.setStyleSheet("""
            QDialog {
                background-color: #121212;
            }
        """)