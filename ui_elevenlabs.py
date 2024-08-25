# ui_elevenlabs.py
import tkinter as tk
from tkinter import messagebox
import elevenlabs_api
import io
from pygame import mixer

# Initialize pygame mixer for audio playback
mixer.init()

def generate_and_play():
    # Get the text from the input field
    text = text_input.get("1.0", tk.END).strip()

    if not text:
        messagebox.showerror("Error", "Please enter text to generate speech.")
        return

    try:
        # Generate audio using the Elevenlabs API
        audio = elevenlabs_api.generate_audio(text)

        # Play the audio using pygame mixer
        audio_io = io.BytesIO(audio)
        mixer.music.load(audio_io, 'mp3')
        mixer.music.play()

        messagebox.showinfo("Success", "Audio generated and played successfully!")

    except Exception as e:
        messagebox.showerror("Error", f"An error occurred: {str(e)}")

# Draw the app window
app = tk.Tk()
app.title("Elevenlabs Test")
app.geometry("512x512")

# Add a text input widget
text_label = tk.Label(app, text="Enter text to convert to speech:")
text_label.pack(pady=10)

text_input = tk.Text(app, height=20, width=60)
text_input.pack(pady=10)

# Add a button to trigger audio generation
generate_button = tk.Button(app, text="Generate Speech", command=generate_and_play)
generate_button.pack(pady=20)

# Start the main loop
app.mainloop()