# openai_api.py
from openai import OpenAI
import openai
import dotenv
import os
import json

# Load environment variables
dotenv.load_dotenv()

openai_api_key = os.getenv('OPENAI_API_KEY')
if not openai_api_key:
    exit("No OpenAI API Key found.")
print("OpenAI API Key loaded successfully.")
client = OpenAI(api_key=openai_api_key)

MODEL = "gpt-4o"

# Function to load memory for a character
def load_memory(character_file):
    memory_file = os.path.join("../characterdata", f"{character_file}_mem.json")
    if os.path.exists(memory_file):
        with open(memory_file, "r") as file:
            return json.load(file)
    else:
        return {"short_term": [], "long_term": []}

# Function to save memory for a character
def save_memory(character_file, memory):
    memory_file = os.path.join("../characterdata", f"{character_file}_mem.json")
    with open(memory_file, "w") as file:
        json.dump(memory, file, indent=4)

# Function to update memory
def update_memory(character_file, memory, new_entry):
    # Add new entry to short-term memory
    memory['short_term'].append(new_entry)
    
    # Keep only the latest 5 entries in short-term memory
    memory['short_term'] = memory['short_term'][-5:]  # Keeping the latest 5 interactions
    
    # Optionally, move older entries to long-term memory
    if len(memory['short_term']) > 3:
        memory['long_term'].append(memory['short_term'].pop(0))
    
    save_memory(character_file, memory)

# Function to handle queries with character memory integration
def get_query(query, character_file, character_data):
    # Load memory for the character
    memory = load_memory(character_file)
    
    # Combine short-term and long-term memory into the conversation context
    # Convert each memory entry (which is a dict) to a string
    memory_entries = [f"User: {entry['query']}\nAssistant: {entry['response']}" for entry in memory['long_term'] + memory['short_term']]
    memory_context = "\n".join(memory_entries)
    
    # Prepare the messages with memory
    messages = [
        {
            "role": "system",
            "content": character_data  # Load character data here
        },
        {
            "role": "assistant",
            "content": f"Memory:\n{memory_context}"  # Include memory in the conversation context
        },
        {
            "role": "user",
            "content": query
        }
    ]
    
    # Get response from OpenAI API
    completion = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        max_tokens=100
    )
    
    # Update memory with the new interaction
    response = completion.choices[0].message.content
    update_memory(character_file, memory, {"query": query, "response": response})
    
    return response