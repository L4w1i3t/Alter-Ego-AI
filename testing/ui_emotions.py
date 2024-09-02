import os
import sys
import tkinter as tk
from tkinter import messagebox
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from api import emotions_api

def detect_emotions():
    # Get the text from the input field
    text = text_input.get("1.0", tk.END).strip()

    if not text:
        messagebox.showerror("Error", "Please enter text to detect emotions.")
        return

    try:
        # Detect emotions using the emotions API
        emotions = emotions_api.detect_emotions([text])

        # Clear previous results
        result_output.delete(1.0, tk.END)

        # Display the detected emotions in the text output widget
        if emotions and emotions[0]:
            for emotion, score in emotions[0].items():
                result_output.insert(tk.END, f"{emotion.capitalize()}: {score:.2f}\n")
        else:
            result_output.insert(tk.END, "No significant emotions detected.")

    except Exception as e:
        messagebox.showerror("Error", f"An error occurred: {str(e)}")

# Draw the app window
app = tk.Tk()
app.title("Emotion API Test")
app.geometry("512x512")

# Add a text input widget
text_label = tk.Label(app, text="Enter text to detect emotions:")
text_label.pack(pady=10)

text_input = tk.Text(app, height=10, width=60)
text_input.pack(pady=10)

# Add a button to trigger emotion detection
detect_button = tk.Button(app, text="Detect Emotions", command=detect_emotions)
detect_button.pack(pady=20)

# Add a text output widget to display the detected emotions
result_label = tk.Label(app, text="Detected Emotions:")
result_label.pack(pady=10)

result_output = tk.Text(app, height=10, width=60, state=tk.NORMAL)
result_output.pack(pady=10)

# Start the main loop
app.mainloop()