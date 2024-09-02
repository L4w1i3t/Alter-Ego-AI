# avatar.py
import os
import tkinter as tk
from PIL import Image, ImageTk

class AvatarWindow:
    # Default image
    def __init__(self, parent_frame, default_image="neutral.png"):
        self.parent_frame = parent_frame
        self.avatar_image = None
        self.image_label = tk.Label(self.parent_frame, bg="#0D0D0D")
        self.image_label.pack(expand=True, fill="both")
        self.original_image = None  # To store the original image for resizing
        self.load_image(default_image)

        # Bind the parent frame resizing event to dynamically resize the image
        self.parent_frame.bind("<Configure>", self.on_resize)

    def load_image(self, image_name):
        try:
            img_path = os.path.join(os.path.dirname(__file__), "sprites", image_name)
            img = Image.open(img_path)

            # Store the original image and its size
            self.original_image = img
            img_width, img_height = img.size

            # Display the initial image
            self.update_image(img_width, img_height)
        except Exception as e:
            print(f"Error loading image {image_name}: {e}")

    def update_image(self, new_width, new_height):
        if self.original_image is not None:
            # Maintain aspect ratio
            aspect_ratio = self.original_image.width / self.original_image.height

            # Calculate new width and height while maintaining aspect ratio
            if new_width / new_height > aspect_ratio:
                new_width = int(new_height * aspect_ratio)
            else:
                new_height = int(new_width / aspect_ratio)

            # Resize the image to fit the window while maintaining the aspect ratio
            resized_image = self.original_image.resize((new_width, new_height), Image.LANCZOS)
            self.avatar_image = ImageTk.PhotoImage(resized_image)

            # Calculate padding to center the image
            x_padding = (self.parent_frame.winfo_width() - new_width) // 2
            y_padding = (self.parent_frame.winfo_height() - new_height) // 2

            # Apply padding to keep the image centered
            self.image_label.config(image=self.avatar_image, padx=x_padding, pady=y_padding)

    def on_resize(self, event):
        new_width = event.width
        new_height = event.height
        self.update_image(new_width, new_height)