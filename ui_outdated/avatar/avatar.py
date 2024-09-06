from PyQt5.QtWidgets import QLabel
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt

class AvatarWindow(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setPixmap(QPixmap("gui/avatar/sprites/neutral.png").scaled(200, 200, aspectRatioMode=True))
        self.setAlignment(Qt.AlignCenter)

    def update_avatar(self, emotions):
        # Update avatar based on the detected emotions
        if "joy" in emotions:
            self.setPixmap(QPixmap("gui/avatar/sprites/joy.png").scaled(200, 200, aspectRatioMode=True))
        elif "anger" in emotions:
            self.setPixmap(QPixmap("gui/avatar/sprites/anger.png").scaled(200, 200, aspectRatioMode=True))
        else:
            self.setPixmap(QPixmap("gui/avatar/sprites/neutral.png").scaled(200, 200, aspectRatioMode=True))
