# openai_api.py
import openai
import dotenv
import os
import json
from tiktoken import encoding_for_model

# Load environment variables
dotenv.load_dotenv()

openai_api_key = os.getenv('OPENAI_API_KEY')
if not openai_api_key:
    exit("No OpenAI API Key found.")
print("OpenAI API Key loaded successfully.")
client = openai.OpenAI(api_key=openai_api_key)

MODEL = "gpt-4o-2024-08-06"

# Base directory for character data
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CHARACTER_DATA_DIR = os.path.join(BASE_DIR, "../characterdata")

# Load memory for a character
def load_memory(character_file):
    memory_file = os.path.join(CHARACTER_DATA_DIR, f"{character_file}_mem.json")
    if os.path.exists(memory_file):
        with open(memory_file, "r") as file:
            return json.load(file)
    else:
        # Return default memory structure if the file does not exist
        return {"short_term": [], "long_term": []}

# Function to save memory for a character
def save_memory(character_file, memory):
    memory_file = os.path.join(CHARACTER_DATA_DIR, f"{character_file}_mem.json")
    with open(memory_file, "w") as file:
        json.dump(memory, file, indent=4)

# Function to update memory
def update_memory(character_file, memory, new_entry):
    # Add new entry to short-term memory
    memory['short_term'].append(new_entry)
    
    # Keep only the latest 5 entries in short-term memory
    memory['short_term'] = memory['short_term'][-5:]  # Keeping the latest 5 interactions
    
    # Move older entries to long-term memory
    if len(memory['short_term']) > 4:
        memory['long_term'].append(memory['short_term'].pop(0))
    
    save_memory(character_file, memory)

def summarize_memory(memory):
    # Summarize long-term memory into a single string
    return f"Summarized interactions: {len(memory['long_term'])} important interactions."

# Function to handle queries with character memory integration
def get_query(query, character_file, character_data):
    memory = load_memory(character_file)
    
    # Combine short-term and long-term memory into the conversation context
    # Convert each memory dict to a string
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
            "content": f"Memory Summary:\n{memory_context}"
        },
        {
            "role": "user",
            "content": query
        }
    ]

    enc = encoding_for_model("gpt-4")
    input_text = "\n".join([message['content'] for message in messages])  # Concatenate all input text
    token_count = len(enc.encode(input_text))
    print(f"Tokens used for this query: {token_count}")
    
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