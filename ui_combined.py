# ui_combined.py
# THIS IS THE SCRIPT THAT SHOULD EXECUTE
import os
import azure.cognitiveservices.speech as speechsdk
import dotenv
from pynput import keyboard
import tkinter as tk
from tkinter import messagebox, END, StringVar
from openai_api import get_query
from azure_stt_api import speech_config
import elevenlabs_api
import io
from pygame import mixer
import threading
from datetime import datetime

# Load environment variables
dotenv.load_dotenv()

# Initialize pygame mixer for audio playback
mixer.init()

# Directory to save response history
RESPONSE_HISTORY_DIR = os.path.join(os.getcwd(), "responsehistory")

# Ensure responsehistory directory exists
os.makedirs(RESPONSE_HISTORY_DIR, exist_ok=True)

# Directory for character data
CHARACTER_DATA_DIR = os.path.join(os.getcwd(), "characterdata")

# Colors and fonts for a hacker aesthetic cause why not
BACKGROUND_COLOR = "#000000"
TEXT_COLOR = "#00FF00"
BUTTON_COLOR = "#003300"
FONT = ("Courier", 12)
BUTTON_FONT = ("Courier", 12, "bold")

recognition_active = False
speech_recognizer = None
selected_character_data = ""

# Function to load character data
def load_character_data(character_file):
    try:
        character_path = os.path.join(CHARACTER_DATA_DIR, character_file)
        with open(character_path, "r") as file:
            return file.read()
    except Exception as e:
        messagebox.showerror("Error", f"An error occurred while loading character data: {str(e)}")
        return ""

# Function to handle character selection change
def on_character_select(selection):
    global selected_character_data
    selected_character_data = load_character_data(selection)

# Draw the app window
app = tk.Tk()
app.title("ALTER EGO")
app.geometry("1280x720")
app.configure(bg=BACKGROUND_COLOR)

# Character selection container frame
character_frame = tk.Frame(app, bg=BACKGROUND_COLOR)
character_frame.grid(row=0, column=0, padx=20, pady=10, sticky="w", columnspan=2)

# Character selection section
character_section_label = tk.Label(character_frame, text="Select Character Data", font=("Courier", 14, "bold"), bg=BACKGROUND_COLOR, fg=TEXT_COLOR)
character_section_label.grid(row=0, column=0, padx=10, pady=5, sticky="w")

character_files = [f for f in os.listdir(CHARACTER_DATA_DIR) if f.endswith('.pers')]
selected_character = StringVar(app)
selected_character.set(character_files[0])  # Default selection

# Create a dropdown menu for character selection
character_dropdown = tk.OptionMenu(character_frame, selected_character, *character_files, command=on_character_select)
character_dropdown.config(font=FONT, bg=BUTTON_COLOR, fg=TEXT_COLOR, highlightthickness=0)
character_dropdown["menu"].config(font=FONT, bg=BACKGROUND_COLOR, fg=TEXT_COLOR)
character_dropdown.grid(row=0, column=1, padx=10, pady=5, sticky="w")

# Load the initial character data
selected_character_data = load_character_data(character_files[0])

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
            # Get response from OpenAI API with selected character data
            response = get_query(question, selected_character_data)
            
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

        # Save audio file if saving is enabled
        if save_audio_enabled.get():
            save_audio_file(audio)

    except Exception as e:
        messagebox.showerror("Error", f"An error occurred: {str(e)}")

# Function to save the audio file to the responsehistory folder
def save_audio_file(audio):
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_name = f"response_{timestamp}.mp3"
        file_path = os.path.join(RESPONSE_HISTORY_DIR, file_name)

        with open(file_path, "wb") as f:
            f.write(audio)

        print(f"Audio saved to {file_path}")

    except Exception as e:
        messagebox.showerror("Error", f"An error occurred while saving the audio: {str(e)}")

# Function to clear all files in the responsehistory folder
def clear_response_history():
    try:
        for file_name in os.listdir(RESPONSE_HISTORY_DIR):
            file_path = os.path.join(RESPONSE_HISTORY_DIR, file_name)
            if os.path.isfile(file_path):
                os.remove(file_path)
        
        messagebox.showinfo("Clear Response History", "All files in the responsehistory folder have been deleted.")
    except Exception as e:
        messagebox.showerror("Error", f"An error occurred while clearing the response history: {str(e)}")

# Function to toggle the settings menu visibility
def toggle_settings_menu():
    if settings_frame.winfo_ismapped():
        settings_frame.grid_remove()
    else:
        settings_frame.grid()

# Initialize BooleanVar after the root window is created
elevenlabs_enabled = tk.BooleanVar(value=True)  # Variable to track ElevenLabs API usage
save_audio_enabled = tk.BooleanVar(value=False)  # Variable to track saving audio files

# Configure dynamic res
app.grid_rowconfigure(1, weight=1)
app.grid_rowconfigure(2, weight=5)
app.grid_rowconfigure(3, weight=1)
app.grid_columnconfigure(0, weight=1)

# Input frame
input_frame = tk.Frame(app, bg=BACKGROUND_COLOR)
input_frame.grid(row=1, column=0, padx=20, pady=20, sticky="nsew")
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
output_text.grid(row=2, column=0, padx=20, pady=20, sticky="nsew")

# Make the output text widget read-only
output_text.config(state=tk.DISABLED)

# Bottom frame for speech recognition status and settings menu button
bottom_frame = tk.Frame(app, bg=BACKGROUND_COLOR)
bottom_frame.grid(row=3, column=0, padx=20, pady=20, sticky="nsew")

recognition_status_label = tk.Label(bottom_frame, text="Speech Recognition (F4): OFF", font=FONT, bg=BACKGROUND_COLOR, fg="red")
recognition_status_label.pack(side="left", padx=10)

# Hamburger menu button to toggle settings menu
hamburger_button = tk.Button(bottom_frame, text="≡", font=BUTTON_FONT, bg=BUTTON_COLOR, fg=TEXT_COLOR, activebackground="#004400", activeforeground=TEXT_COLOR, borderwidth=2, relief="ridge", command=toggle_settings_menu)
hamburger_button.pack(side="right", padx=10)

# Settings frame for the side panel
settings_frame = tk.Frame(app, bg=BACKGROUND_COLOR, bd=2, relief="sunken")
settings_frame.grid(row=0, column=1, rowspan=4, sticky="nsew", padx=10, pady=10)
settings_frame.grid_remove()  # Initially hidden

# Settings options inside the settings frame
elevenlabs_toggle = tk.Checkbutton(settings_frame, text="Enable Speech Audio", variable=elevenlabs_enabled, font=FONT, bg=BACKGROUND_COLOR, fg=TEXT_COLOR, selectcolor=BUTTON_COLOR)
elevenlabs_toggle.pack(anchor="w", pady=5)

save_audio_toggle = tk.Checkbutton(settings_frame, text="Save Audio Files", variable=save_audio_enabled, font=FONT, bg=BACKGROUND_COLOR, fg=TEXT_COLOR, selectcolor=BUTTON_COLOR)
save_audio_toggle.pack(anchor="w", pady=5)

clear_history_button = tk.Button(settings_frame, text="Clear Response History", command=clear_response_history, font=BUTTON_FONT, bg=BUTTON_COLOR, fg=TEXT_COLOR, activebackground="#004400", activeforeground=TEXT_COLOR, borderwidth=2, relief="ridge")
clear_history_button.pack(anchor="w", pady=5)

app.mainloop()