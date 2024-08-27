# ui_azure.py
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import azure.cognitiveservices.speech as speechsdk
from api.azure_stt_api import speech_config
import tkinter as tk
from pynput import keyboard

print("---------------------------------------------------------")
print("Program now online. Press F4 or hit \"Start Recognition\" to enable speech recognition.")

# Flag to track the state of speech recognition
recognizing = False
speech_recognizer = None

# Initialize
app = tk.Tk()
app.title("Azure Test")
app.geometry("512x512")

# Text widget to display recognized speech
output_text = tk.Text(app, height=20, width=60)
output_text.pack(pady=10)

# Function to start speech recognition
def start_recognition():
    global speech_recognizer
    speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config)

    def recognized_callback(evt):
        if evt.result.reason == speechsdk.ResultReason.RecognizedSpeech:
            output_text.insert(tk.END, f"Recognized: {evt.result.text}\n")
            output_text.see(tk.END)  # Auto-scroll to the latest entry
        elif evt.result.reason == speechsdk.ResultReason.NoMatch:
            output_text.insert(tk.END, "No speech recognized.\n")
            output_text.see(tk.END)

    def canceled_callback(evt):
        output_text.insert(tk.END, f"Speech Recognition canceled: {evt.result.reason}\n")
        if evt.result.reason == speechsdk.CancellationReason.Error:
            output_text.insert(tk.END, f"Error details: {evt.result.error_details}\n")
        output_text.see(tk.END)

    # Connect callbacks to the events fired by the speech recognizer
    speech_recognizer.recognized.connect(recognized_callback)
    speech_recognizer.canceled.connect(canceled_callback)

    output_text.insert(tk.END, "Starting continuous speech recognition...\n")
    output_text.see(tk.END)
    speech_recognizer.start_continuous_recognition()

def stop_recognition():
    if speech_recognizer:
        output_text.insert(tk.END, "Stopping continuous speech recognition...\n")
        output_text.see(tk.END)
        speech_recognizer.stop_continuous_recognition()

def on_toggle():
    global recognizing
    if not recognizing:
        recognizing = True
        start_recognition()
        toggle_button.config(text="Stop Recognition")
    else:
        recognizing = False
        stop_recognition()
        toggle_button.config(text="Start Recognition")

def on_press(key):
    try:
        if key == keyboard.Key.f4:
            on_toggle()
    except AttributeError:
        pass

# Add a button to toggle recognition
toggle_button = tk.Button(app, text="Start Recognition", command=on_toggle)
toggle_button.pack(pady=20)

# Set up a keyboard listener to handle F4 key press
listener = keyboard.Listener(on_press=on_press)
listener.start()

# Start the GUI event loop
app.mainloop()