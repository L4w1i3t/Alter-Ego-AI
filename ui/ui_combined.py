# ui_combined.py
import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"

import sys
import warnings
warnings.filterwarnings("ignore")

import threading
import time
import io
import shutil
from datetime import datetime
import tkinter as tk
from tkinter import messagebox, END, StringVar
from pynput import keyboard
from pygame import mixer
import dotenv
import azure.cognitiveservices.speech as speechsdk

# Add the parent directory to sys.path for module imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import custom modules
from api.openai_api import get_query, load_memory, save_memory
from api.azure_stt_api import speech_config
from api import elevenlabs_api
from api.emotions_api import detect_emotions
from avatar import AvatarWindow

# Load environment variables
dotenv.load_dotenv()

# Initialize mixer
mixer.init()

# Directories and paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RESPONSE_HISTORY_DIR = os.path.join(BASE_DIR, "../responsehistory")
CHARACTER_DATA_DIR = os.path.join(BASE_DIR, "../characterdata")
os.makedirs(RESPONSE_HISTORY_DIR, exist_ok=True)

# UI Constants
BACKGROUND_COLOR = "#0D0D0D"
TEXT_COLOR = "#00FF00"
BUTTON_COLOR = "#004400"
FONT = ("Courier New", 12)
BUTTON_FONT = ("Courier New", 12, "bold")

# Global variables
recognition_active = False
speech_recognizer = None
selected_character_data = ""
avatar_window = None
query_lock = threading.Lock()

# Helper Functions
def load_character_data(character_file):
    file_path = os.path.join(CHARACTER_DATA_DIR, character_file)
    try:
        with open(file_path, "r") as file:
            return file.read()
    except Exception as e:
        messagebox.showerror("Error", f"Error loading character data: {str(e)}")
        return ""

def clear_response_history():
    try:
        shutil.rmtree(RESPONSE_HISTORY_DIR)
        os.makedirs(RESPONSE_HISTORY_DIR)
        messagebox.showinfo("Clear Response History", "All response history files have been deleted.")
    except Exception as e:
        messagebox.showerror("Error", f"Error clearing response history: {str(e)}")

def save_response_data(prompt, response):
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        response_folder = os.path.join(RESPONSE_HISTORY_DIR, f"response_{timestamp}")
        os.makedirs(response_folder, exist_ok=True)

        with open(os.path.join(response_folder, "prompt.txt"), "w") as f:
            f.write(f"Prompt: {prompt}\n")
        with open(os.path.join(response_folder, "response.txt"), "w") as f:
            f.write(f"Response: {response}\n")

        if elevenlabs_enabled.get():
            audio = elevenlabs_api.generate_audio(response)
            with open(os.path.join(response_folder, "response.mp3"), "wb") as f:
                f.write(audio)

    except Exception as e:
        messagebox.showerror("Error", f"Error saving response data: {str(e)}")

# UI Update Functions
def update_recognition_status():
    recognition_status_label.config(
        text=f"Speech Recognition (F4): {'ON' if recognition_active else 'OFF'}",
        fg="lime" if recognition_active else "red"
    )

def animate_text(widget, text, delay=0.01):
    widget.config(state=tk.NORMAL)
    widget.delete(1.0, END)
    for char in text:
        widget.insert(END, char)
        widget.update_idletasks()
        time.sleep(delay)
    widget.config(state=tk.DISABLED)
    entry.config(state=tk.NORMAL)
    submit_button.config(state=tk.NORMAL)

def display_emotions(emotions):
    emotions_text.config(state=tk.NORMAL)
    emotions_text.delete(1.0, END)
    if emotions:
        emotions_text.insert(END, "Detected Emotions:\n\n")
        for emotion, score in emotions.items():
            emotions_text.insert(END, f"{emotion.capitalize()}: {score:.2f}\n")
    else:
        emotions_text.insert(END, "No significant emotions detected.")
    emotions_text.config(state=tk.DISABLED)

# Event Handlers
def on_character_select(selection):
    global selected_character_data
    selected_character_data = load_character_data(selection)

def on_voice_model_select(selection):
    try:
        elevenlabs_api.change_voice_model(selection)
    except Exception as e:
        messagebox.showerror("Error", f"Error changing voice model: {str(e)}")

def on_submit():
    question = entry.get().strip()
    if question:
        entry.delete(0, END)
        output_text.config(state=tk.NORMAL)
        output_text.delete(1.0, END)
        output_text.insert(END, "Thinking...")
        output_text.config(state=tk.DISABLED)

        entry.config(state=tk.DISABLED)
        submit_button.config(state=tk.DISABLED)

        threading.Thread(target=generate_response, args=(question,), daemon=True).start()

def on_emotion_toggle():
    if not detect_emotions_enabled.get():
        emotions_text.config(state=tk.NORMAL)
        emotions_text.delete(1.0, END)
        emotions_text.insert(END, "[EMOTION DETECTION DISABLED]")
        emotions_text.config(state=tk.DISABLED)
    else:
        emotions_text.config(state=tk.NORMAL)
        emotions_text.delete(1.0, END)
        emotions_text.config(state=tk.DISABLED)

def on_press(key):
    global recognition_active

    if key == keyboard.Key.f4:
        recognition_active = not recognition_active
        update_recognition_status()
        if recognition_active:
            threading.Thread(target=continuous_recognition, daemon=True).start()

def on_enter(event):
    on_submit()

def toggle_settings_menu():
    if settings_frame.winfo_ismapped():
        settings_frame.grid_remove()
    else:
        settings_frame.grid()

def generate_and_play(response):
    try:
        audio = elevenlabs_api.generate_audio(response)
        audio_io = io.BytesIO(audio)
        mixer.music.load(audio_io, 'mp3')
        mixer.music.play()
    except Exception as e:
        messagebox.showerror("Error", f"Error generating or playing audio: {str(e)}")

# Core Functions
def continuous_recognition():
    global recognition_active
    global speech_recognizer

    def recognized_cb(evt):
        entry.insert(END, evt.result.text)
        on_submit()

    try:
        speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config)
        speech_recognizer.recognized.connect(recognized_cb)
        speech_recognizer.start_continuous_recognition()

        while recognition_active:
            time.sleep(0.1)

        speech_recognizer.stop_continuous_recognition()
    except Exception as e:
        messagebox.showerror("Error", f"Speech recognition error: {str(e)}")

def generate_response(question):
    if not query_lock.acquire(blocking=False):
        messagebox.showerror("Error", "Please wait for the current response to finish.")
        return

    try:
        response = get_query(question, selected_character.get(), selected_character_data)

        def animate_and_display_emotions():
            animate_text(output_text, response)
            if detect_emotions_enabled.get():
                emotions = detect_emotions([response])
                display_emotions(emotions[0])

        threading.Thread(target=animate_and_display_emotions, daemon=True).start()

        if elevenlabs_enabled.get():
            generate_and_play(response)

        if save_query_enabled.get():
            save_response_data(question, response)

    except Exception as e:
        messagebox.showerror("Error", f"An error occurred: {str(e)}")
    finally:
        entry.delete(0, END)
        query_lock.release()

# Initialize the main application window
app = tk.Tk()
app.title("ALTER EGO")
app.geometry("1280x720")
app.configure(bg=BACKGROUND_COLOR)

# Frame for the avatar display
avatar_frame = tk.Frame(app, bg=BACKGROUND_COLOR, width=300, height=300)
avatar_frame.grid(row=0, column=1, rowspan=4, sticky="nsew", padx=10, pady=10)
avatar_window = AvatarWindow(avatar_frame)

# Global variable for selected character
character_files = [f for f in os.listdir(CHARACTER_DATA_DIR) if f.endswith('.chr')]
if not character_files:
    messagebox.showerror("NO CHARACTER DATA FOUND", "No .chr files found. Exiting...")
    sys.exit()

selected_character = StringVar(app, character_files[0])
selected_character_data = load_character_data(character_files[0])

# Layout: Character and Voice Model Selection
character_frame = tk.Frame(app, bg=BACKGROUND_COLOR)
character_frame.grid(row=0, column=0, padx=20, pady=10, sticky="w", columnspan=2)

tk.Label(character_frame, text="Select Character Data", font=("Courier New", 14, "bold italic"), bg=BACKGROUND_COLOR, fg=TEXT_COLOR).grid(row=0, column=0, padx=10, pady=5, sticky="w")
character_dropdown = tk.OptionMenu(character_frame, selected_character, *character_files, command=on_character_select)
character_dropdown.config(font=FONT, bg=BUTTON_COLOR, fg=TEXT_COLOR, highlightthickness=0)
character_dropdown["menu"].config(font=FONT, bg=BACKGROUND_COLOR, fg=TEXT_COLOR)
character_dropdown.grid(row=0, column=1, padx=10, pady=5, sticky="w")

# Load available voice models
voice_models = list(elevenlabs_api.voice_models.keys())
selected_voice_model = StringVar(app, voice_models[0])
tk.Label(character_frame, text="Select Voice Model", font=("Courier New", 14, " bold italic"), bg=BACKGROUND_COLOR, fg=TEXT_COLOR).grid(row=1, column=0, padx=10, pady=5, sticky="w")
voice_model_dropdown = tk.OptionMenu(character_frame, selected_voice_model, *voice_models, command=on_voice_model_select)
voice_model_dropdown.config(font=FONT, bg=BUTTON_COLOR, fg=TEXT_COLOR, highlightthickness=0)
voice_model_dropdown["menu"].config(font=FONT, bg=BACKGROUND_COLOR, fg=TEXT_COLOR)
voice_model_dropdown.grid(row=1, column=1, padx=10, pady=5, sticky="w")

# Layout: Input Frame
input_frame = tk.Frame(app, bg=BACKGROUND_COLOR)
input_frame.grid(row=1, column=0, padx=20, pady=(0, 10), sticky="nsew")  
input_frame.grid_columnconfigure(0, weight=1)

tk.Label(input_frame, text="Enter your query:", font=FONT, bg=BACKGROUND_COLOR, fg=TEXT_COLOR).grid(row=0, column=0, padx=10, pady=5, sticky="w")  
entry = tk.Entry(input_frame, font=FONT, bg="#001100", fg=TEXT_COLOR, insertbackground=TEXT_COLOR, borderwidth=2, relief="sunken")
entry.grid(row=1, column=0, padx=10, pady=5, sticky="ew")  
entry.bind("<Return>", on_enter)
submit_button = tk.Button(input_frame, text="Submit", command=on_submit, font=BUTTON_FONT, bg=BUTTON_COLOR, fg=TEXT_COLOR, activebackground="#004400", activeforeground=TEXT_COLOR, borderwidth=2, relief="ridge")
submit_button.grid(row=1, column=1, padx=10, pady=10, sticky="w")  

# Layout: Output Area
output_frame = tk.Frame(app, bg=BACKGROUND_COLOR)
output_frame.grid(row=2, column=0, padx=20, pady=0, sticky="nsew")  
output_frame.grid_columnconfigure(0, weight=1)
output_frame.grid_rowconfigure(0, weight=1) 

output_text = tk.Text(output_frame, font=FONT, bg="#001100", fg=TEXT_COLOR, wrap="word", insertbackground=TEXT_COLOR, borderwidth=2, relief="sunken")
output_text.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
output_text.config(state=tk.DISABLED)

# Layout: Bottom Frame
bottom_frame = tk.Frame(app, bg=BACKGROUND_COLOR)
bottom_frame.grid(row=3, column=0, padx=20, pady=(0, 20), sticky="nsew")  

recognition_status_label = tk.Label(bottom_frame, text="Speech Recognition (F4): OFF", font=FONT, bg=BACKGROUND_COLOR, fg="red")
recognition_status_label.pack(side="left", padx=10)

tk.Button(bottom_frame, text="≡", font=BUTTON_FONT, bg=BUTTON_COLOR, fg=TEXT_COLOR, activebackground="#004400", activeforeground=TEXT_COLOR, borderwidth=2, relief="ridge", command=toggle_settings_menu).pack(side="right", padx=10)

emotions_text = tk.Text(bottom_frame, font=FONT, bg="#110000", fg="#FF6347", wrap="word", insertbackground="#FF6347", borderwidth=2, relief="sunken", height=5, width=40)
emotions_text.pack(side="right", padx=10, pady=10)
emotions_text.config(state=tk.DISABLED)

# Layout: Settings Frame
settings_frame = tk.Frame(app, bg=BACKGROUND_COLOR, bd=2, relief="sunken")
settings_frame.grid(row=0, column=2, rowspan=4, sticky="nsew", padx=10, pady=10)
settings_frame.grid_remove()

elevenlabs_enabled = tk.BooleanVar(value=True)
save_query_enabled = tk.BooleanVar(value=False)
detect_emotions_enabled = tk.BooleanVar(value=True)
tk.Checkbutton(settings_frame, text="Response Emotions", variable=detect_emotions_enabled, font=FONT, bg=BACKGROUND_COLOR, fg=TEXT_COLOR, selectcolor=BUTTON_COLOR, command=on_emotion_toggle).pack(anchor="w", pady=5)
tk.Checkbutton(settings_frame, text="Response Audio", variable=elevenlabs_enabled, font=FONT, bg=BACKGROUND_COLOR, fg=TEXT_COLOR, selectcolor=BUTTON_COLOR).pack(anchor="w", pady=5)
tk.Checkbutton(settings_frame, text="Save History", variable=save_query_enabled, font=FONT, bg=BACKGROUND_COLOR, fg=TEXT_COLOR, selectcolor=BUTTON_COLOR).pack(anchor="w", pady=5)
tk.Button(settings_frame, text="Clear Response History", command=clear_response_history, font=BUTTON_FONT, bg=BUTTON_COLOR, fg=TEXT_COLOR, activebackground="#004400", activeforeground=TEXT_COLOR, borderwidth=2, relief="ridge").pack(anchor="w", pady=5)

app.grid_rowconfigure(1, weight=1)
app.grid_rowconfigure(2, weight=5)
app.grid_rowconfigure(3, weight=1)
app.grid_columnconfigure(0, weight=1)
app.grid_columnconfigure(1, weight=1)

# Start app
keyboard.Listener(on_press=on_press).start()
app.mainloop()
