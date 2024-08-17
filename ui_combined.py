import tkinter as tk
from tkinter import messagebox, END
from openai_api import get_query
import elevenlabs_api
import io
from pygame import mixer

# Initialize pygame mixer for audio playback
mixer.init()

# Colors and fonts for a hacker aesthetic because why the hell not
BACKGROUND_COLOR = "#000000"
TEXT_COLOR = "#00FF00"
BUTTON_COLOR = "#003300"
FONT = ("Courier", 12) 
BUTTON_FONT = ("Courier", 12, "bold")

def on_submit():
    question = entry.get()
    if question.strip():
        try:
            # Get response from OpenAI API
            response = get_query(question)
            output_text.delete(1.0, END)
            output_text.insert(END, response)

            # Automatically generate speech from response using ElevenLabs API
            generate_and_play(response)

        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")

def generate_and_play(text):
    try:
        # Generate audio using the Elevenlabs API
        audio = elevenlabs_api.generate_audio(text)

        # Play the audio using pygame mixer
        audio_io = io.BytesIO(audio)
        mixer.music.load(audio_io, 'mp3')
        mixer.music.play()

    except Exception as e:
        messagebox.showerror("Error", f"An error occurred: {str(e)}")

# Draw the app window
app = tk.Tk()
app.title("Hacker Assistant - OpenAI + ElevenLabs")
app.geometry("800x600")
app.configure(bg=BACKGROUND_COLOR)

# Configure dynamic res
app.grid_rowconfigure(0, weight=1)
app.grid_rowconfigure(1, weight=5)
app.grid_rowconfigure(2, weight=1)
app.grid_columnconfigure(0, weight=1)

# Input
input_frame = tk.Frame(app, bg=BACKGROUND_COLOR)
input_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
label = tk.Label(input_frame, text="Enter your query:", font=FONT, bg=BACKGROUND_COLOR, fg=TEXT_COLOR)
label.grid(row=0, column=0, padx=10, pady=10, sticky="w")

entry = tk.Entry(input_frame, font=FONT, bg="#001100", fg=TEXT_COLOR, insertbackground=TEXT_COLOR, borderwidth=2, relief="sunken")
entry.grid(row=1, column=0, padx=10, pady=10, sticky="ew")

submit_button = tk.Button(input_frame, text="Submit", command=on_submit, font=BUTTON_FONT, bg=BUTTON_COLOR, fg=TEXT_COLOR, activebackground="#004400", activeforeground=TEXT_COLOR, borderwidth=2, relief="ridge")
submit_button.grid(row=1, column=1, padx=10, pady=10, sticky="w")

input_frame.grid_columnconfigure(0, weight=1)

# Output area to display the response from OpenAI API
output_text = tk.Text(app, font=FONT, bg="#001100", fg=TEXT_COLOR, wrap="word", insertbackground=TEXT_COLOR, borderwidth=2, relief="sunken")
output_text.grid(row=1, column=0, padx=20, pady=20, sticky="nsew")

bottom_frame = tk.Frame(app, bg=BACKGROUND_COLOR)
bottom_frame.grid(row=2, column=0, padx=20, pady=20, sticky="nsew")

app.mainloop()