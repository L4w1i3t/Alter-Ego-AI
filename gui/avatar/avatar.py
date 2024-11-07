# avatar/avatar.py
import os
from PyQt5.QtWidgets import QLabel
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt


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
            os.path.dirname(__file__), "sprites", self.character_folder
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
