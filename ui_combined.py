import os
import azure.cognitiveservices.speech as speechsdk
import dotenv
from pynput import keyboard
import tkinter as tk
from tkinter import messagebox, END
from openai_api import get_query
from azure_stt_api import speech_config
import elevenlabs_api
import io
from pygame import mixer
import threading

# Load environment variables
dotenv.load_dotenv()

# Initialize pygame mixer for audio playback
mixer.init()

# Colors and fonts for a hacker aesthetic cause why not
BACKGROUND_COLOR = "#000000"
TEXT_COLOR = "#00FF00"
BUTTON_COLOR = "#003300"
FONT = ("Courier", 12)
BUTTON_FONT = ("Courier", 12, "bold")

# State variables
recognition_active = False

speech_recognizer = None

# Function to handle continuous speech recognition
def continuous_recognition():
    global speech_recognizer, recognition_active

    # Initialize the Speech Recognizer
    speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config)

    # Callback when recognized speech is detected
    def recognized_cb(evt):
        print(f"Recognized: {evt.result.text}")
        entry.insert(END, evt.result.text)
        on_submit()  # Automatically submit the recognized speech as a query

    # Connect event handlers for recognizing events
    speech_recognizer.recognized.connect(recognized_cb)

    # Start continuous recognition
    speech_recognizer.start_continuous_recognition()

    print("Continuous recognition started...")
    while recognition_active:
        pass  # Keep the thread alive as long as recognition is active

    # Stop recognition when the flag is set to False
    speech_recognizer.stop_continuous_recognition()
    print("Continuous recognition stopped...")

# Function to update the speech recognition status label
def update_recognition_status():
    if recognition_active:
        recognition_status_label.config(text="Speech Recognition (F4): ON", fg="lime")
    else:
        recognition_status_label.config(text="Speech Recognition (F4): OFF", fg="red")

# Function to handle F4 key press
def on_press(key):
    global recognition_active

    try:
        if key == keyboard.Key.f4:
            if not recognition_active:
                recognition_active = True
                update_recognition_status()
                threading.Thread(target=continuous_recognition).start()
            else:
                recognition_active = False
                update_recognition_status()
    except AttributeError:
        pass

# Start listening for key presses
listener = keyboard.Listener(on_press=on_press)
listener.start()

# Function to handle query submission
def on_submit():
    question = entry.get()
    if question.strip():
        try:
            # Get response from OpenAI API
            response = get_query(question)
            
            # Temporarily enable the output_text widget to insert text
            output_text.config(state=tk.NORMAL)
            output_text.delete(1.0, END)
            output_text.insert(END, response)
            # Disable the output_text widget again
            output_text.config(state=tk.DISABLED)

            # Check if ElevenLabs API usage is enabled
            if elevenlabs_enabled.get():
                generate_and_play(response)

        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")

        # Clear the entry box after submitting the query
        entry.delete(0, END)

def on_enter(event):
    on_submit()

# Function to generate and play speech using Elevenlabs API
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
app.title("Test")
app.geometry("1280x720")
app.configure(bg=BACKGROUND_COLOR)

# Initialize BooleanVar after the root window is created
elevenlabs_enabled = tk.BooleanVar(value=True)  # Variable to track ElevenLabs API usage

# Configure dynamic res
app.grid_rowconfigure(0, weight=1)
app.grid_rowconfigure(1, weight=5)
app.grid_rowconfigure(2, weight=1)
app.grid_columnconfigure(0, weight=1)

# Input frame
input_frame = tk.Frame(app, bg=BACKGROUND_COLOR)
input_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
label = tk.Label(input_frame, text="Enter your query:", font=FONT, bg=BACKGROUND_COLOR, fg=TEXT_COLOR)
label.grid(row=0, column=0, padx=10, pady=10, sticky="w")

entry = tk.Entry(input_frame, font=FONT, bg="#001100", fg=TEXT_COLOR, insertbackground=TEXT_COLOR, borderwidth=2, relief="sunken")
entry.grid(row=1, column=0, padx=10, pady=10, sticky="ew")
entry.bind("<Return>", on_enter)  # Bind the Enter key to submit

submit_button = tk.Button(input_frame, text="Submit", command=on_submit, font=BUTTON_FONT, bg=BUTTON_COLOR, fg=TEXT_COLOR, activebackground="#004400", activeforeground=TEXT_COLOR, borderwidth=2, relief="ridge")
submit_button.grid(row=1, column=1, padx=10, pady=10, sticky="w")

input_frame.grid_columnconfigure(0, weight=1)

# Output area to display the response from OpenAI API
output_text = tk.Text(app, font=FONT, bg="#001100", fg=TEXT_COLOR, wrap="word", insertbackground=TEXT_COLOR, borderwidth=2, relief="sunken")
output_text.grid(row=1, column=0, padx=20, pady=20, sticky="nsew")

# Make the output text widget read-only
output_text.config(state=tk.DISABLED)

# Bottom frame for speech recognition status and toggle button
bottom_frame = tk.Frame(app, bg=BACKGROUND_COLOR)
bottom_frame.grid(row=2, column=0, padx=20, pady=20, sticky="nsew")

recognition_status_label = tk.Label(bottom_frame, text="Speech Recognition (F4): OFF", font=FONT, bg=BACKGROUND_COLOR, fg="red")
recognition_status_label.pack(side="left", padx=10)

# Toggle button for ElevenLabs API usage
elevenlabs_toggle = tk.Checkbutton(bottom_frame, text="Enable Speech Audio", variable=elevenlabs_enabled, font=FONT, bg=BACKGROUND_COLOR, fg=TEXT_COLOR, selectcolor=BUTTON_COLOR)
elevenlabs_toggle.pack(side="right", padx=10)

app.mainloop()