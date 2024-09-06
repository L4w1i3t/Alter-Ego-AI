# construct.py
import os
import json
from PyQt5.QtWidgets import (
    QVBoxLayout, QListWidget, QListWidgetItem, 
    QDialog
)

# Dialog to display the chat history
class ChatHistoryDialog(QDialog):
    def __init__(self, character_file):
        super().__init__()
        self.setWindowTitle("Chat History")
        self.setGeometry(100, 100, 1280, 720)
        layout = QVBoxLayout()
        self.chat_history_list = QListWidget()
        layout.addWidget(self.chat_history_list)
        self.load_character_memory(character_file)
        self.setLayout(layout)
        self.setStyleSheet("""
            background-color: black;
            color: #00FF00;
            font-family: 'Courier New', monospace;
        """)

    def load_character_memory(self, character_file):
        memory_file = os.path.join(os.path.dirname(__file__), '../characterdata', f'{character_file}_mem.json')
        if os.path.exists(memory_file):
            with open(memory_file, 'r') as file:
                memory = json.load(file)
                for entry in memory.get('long_term', []):
                    chat_entry = f"User (Long-term): {entry['query']}\n{character_file}: {entry['response']}"
                    self.chat_history_list.addItem(QListWidgetItem(chat_entry))
                for entry in memory.get('short_term', []):
                    chat_entry = f"User (Short-term): {entry['query']}\n{character_file}: {entry['response']}"
                    self.chat_history_list.addItem(QListWidgetItem(chat_entry))
        else:
            self.chat_history_list.addItem(QListWidgetItem("No memory file found for this character."))