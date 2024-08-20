# ui_openai.py
from tkinter import Tk, Label, Entry, Button, Text, END
import tkinter as tk
from openai_api import get_query

def on_submit():
    question = entry.get()
    if question.strip():
        response = get_query(question)
        output_text.delete(1.0, END)
        output_text.insert(END, response)

# Create the UI
app = Tk()
app.title("OpenAI Test")
app.geometry("512x512") 

label = Label(app, text="Enter your query:")
label.pack(pady=10)

entry = Entry(app, width=60)
entry.pack(pady=10)

submit_button = Button(app, text="Submit", command=on_submit)
submit_button.pack(pady=10)

output_text = Text(app, height=20, width=60) 
output_text.pack(pady=10)

app.mainloop()