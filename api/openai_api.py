import openai
import os
import json
import sqlite3
import pickle
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from tiktoken import encoding_for_model
import configparser
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

openai_api_key = os.getenv('OPENAI_API_KEY')
if not openai_api_key:
    exit("No OpenAI API Key found.")
logging.info("OpenAI API Key loaded successfully.")
openai.api_key = openai_api_key

# Load configuration
config = configparser.ConfigParser()
config.read(os.path.join(os.path.dirname(__file__), '../config.ini'))

# Configuration parameters
MODEL = config.get('OpenAI', 'model', fallback='gpt-4o')
SUMMARIZATION_MODEL = config.get('OpenAI', 'summarization_model', fallback='gpt-3.5-turbo')
EMBEDDING_MODEL = config.get('OpenAI', 'embedding_model', fallback='text-embedding-ada-002')
MAX_TOKENS_ALLOWED = config.getint('OpenAI', 'max_tokens_allowed', fallback=2000)
MAX_RESPONSE_TOKENS = config.getint('OpenAI', 'max_response_tokens', fallback=100)
TOP_K = config.getint('Memory', 'top_k', fallback=3)
MAX_SHORT_TERM_MEMORY = config.getint('Memory', 'max_short_term_memory', fallback=5)

# Base directory for character data
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CHARACTER_DATA_DIR = os.path.join(BASE_DIR, "../characterdata")
MEMORY_DB_DIR = os.path.join(BASE_DIR, "../memory_databases")

# Ensure memory database directory exists
if not os.path.exists(MEMORY_DB_DIR):
    os.makedirs(MEMORY_DB_DIR)

# Initialize database for a character
def initialize_database(character_file):
    db_path = os.path.join(MEMORY_DB_DIR, f"{character_file}_memory.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS memory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            query TEXT,
            response TEXT,
            query_embedding BLOB,
            response_embedding BLOB
        )
    ''')
    conn.commit()
    conn.close()
    logging.info(f"Database initialized for character: {character_file}")

# Function to get embeddings
def get_embedding(text):
    response = openai.embeddings.create(
        input=text,
        model=EMBEDDING_MODEL
    )
    embedding = response.data[0].embedding
    return embedding

# Function to add memory entry
def add_memory_entry(character_file, new_entry):
    db_path = os.path.join(MEMORY_DB_DIR, f"{character_file}_memory.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO memory (query, response, query_embedding, response_embedding)
        VALUES (?, ?, ?, ?)
    ''', (
        new_entry['query'],
        new_entry['response'],
        pickle.dumps(new_entry['query_embedding']),
        pickle.dumps(new_entry['response_embedding'])
    ))
    conn.commit()
    conn.close()
    logging.info("New memory entry added.")

# Function to retrieve relevant memories using embeddings
def get_relevant_memories(character_file, query, top_k=TOP_K):
    query_embedding = get_embedding(query)
    db_path = os.path.join(MEMORY_DB_DIR, f"{character_file}_memory.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('SELECT query, response, query_embedding FROM memory')
    all_entries = cursor.fetchall()
    conn.close()
    similarities = []
    for entry_query, entry_response, entry_query_embedding_pickle in all_entries:
        entry_query_embedding = pickle.loads(entry_query_embedding_pickle)
        sim = cosine_similarity(
            [query_embedding],
            [entry_query_embedding]
        )[0][0]
        similarities.append((sim, {'query': entry_query, 'response': entry_response}))
    similarities.sort(key=lambda x: x[0], reverse=True)
    relevant_entries = [entry for _, entry in similarities[:top_k]]
    logging.info(f"Retrieved {len(relevant_entries)} relevant memories.")
    return relevant_entries

# Function to summarize long-term memory
def summarize_memory(character_file):
    db_path = os.path.join(MEMORY_DB_DIR, f"{character_file}_memory.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('SELECT query, response FROM memory')
    all_entries = cursor.fetchall()
    conn.close()
    long_term_entries = [f"User: {entry_query}\nAssistant: {entry_response}" for entry_query, entry_response in all_entries]
    long_term_text = "\n".join(long_term_entries)
    if not long_term_text.strip():
        return "No previous interactions to summarize."
    # Generate a summary before applying to context
    summary_prompt = f"Summarize the following interactions to help you remember important details for future conversations:\n\n{long_term_text}"
    max_summary_tokens = 150  # Adjust based on your needs
    try:
        summary_response = openai.chat.completions.create(
            model=SUMMARIZATION_MODEL,
            messages=[{"role": "user", "content": summary_prompt}],
            max_tokens=max_summary_tokens,
            temperature=0.7
        )
        summary = summary_response.choices[0].message.content.strip()
        logging.info("Long-term memory summarized.")
        return summary
    except Exception as e:
        logging.error(f"Error during memory summarization: {e}")
        return "Could not summarize long-term memory."

# Main function to handle queries with character memory integration
def get_query(query, character_file, character_data):
    # Initialize database if needed
    initialize_database(character_file)

    # Retrieve relevant memories
    relevant_memories = get_relevant_memories(character_file, query)

    # Prepare memory context
    memory_entries = [f"User: {entry['query']}\nAssistant: {entry['response']}" for entry in relevant_memories]
    memory_context = "\n".join(memory_entries)

    # Summarize long-term memory
    long_term_summary = summarize_memory(character_file)

    # Prepare messages
    messages = [
        {
            "role": "system",
            "content": character_data
        },
        {
            "role": "system",
            "content": f"Long-term Memory Summary:\n{long_term_summary}"
        },
        {
            "role": "assistant",
            "content": f"Relevant Previous Interactions:\n{memory_context}"
        },
        {
            "role": "user",
            "content": query
        }
    ]

    # Token counting
    enc = encoding_for_model(MODEL)
    total_tokens = sum(len(enc.encode(message['content'])) for message in messages)

    # Print the number of tokens used before sending the API call
    print(f"Total tokens used before adjustments: {total_tokens}")

    max_tokens_allowed = MAX_TOKENS_ALLOWED - MAX_RESPONSE_TOKENS  # Reserve tokens for the response

    # If over limit, adjust context
    if total_tokens > max_tokens_allowed:
        print(f"Token limit exceeded. Total tokens: {total_tokens}, Max allowed: {max_tokens_allowed}")
        # Remove the least relevant memory entries
        logging.warning("Token limit exceeded, adjusting context by removing least relevant memories.")
        while total_tokens > max_tokens_allowed and relevant_memories:
            relevant_memories.pop()
            memory_entries = [f"User: {entry['query']}\nAssistant: {entry['response']}" for entry in relevant_memories]
            memory_context = "\n".join(memory_entries)
            messages[2]['content'] = f"Relevant Previous Interactions:\n{memory_context}"
            total_tokens = sum(len(enc.encode(message['content'])) for message in messages)

            # Print the number of tokens after removing memories
            print(f"Tokens after memory adjustment: {total_tokens}")

        if total_tokens > max_tokens_allowed:
            # As a last resort, remove the long-term memory summary
            logging.warning("Still over token limit after removing memories, removing long-term memory summary.")
            messages.pop(1)
            total_tokens = sum(len(enc.encode(message['content'])) for message in messages)

            # Print the number of tokens after removing long-term memory summary
            print(f"Tokens after removing long-term memory summary: {total_tokens}")

            if total_tokens > max_tokens_allowed:
                logging.error("Unable to adjust context within token limits.")
                return "I'm sorry, but I'm unable to process your request due to context length limitations."

    # Print the final token count before making the API call
    print(f"Final token count before API call: {total_tokens}")

    # Get response
    try:
        completion = openai.chat.completions.create(
            model=MODEL,
            messages=messages,
            max_tokens=MAX_RESPONSE_TOKENS,
            temperature=0.7
        )
        response = completion.choices[0].message.content.strip()
        logging.info("Received response from OpenAI API.")

        # Print the number of tokens used in the response
        response_tokens = len(enc.encode(response))
        print(f"Tokens used in the response: {response_tokens}")

        # Update memory with the new interaction
        new_entry = {
            "query": query,
            "response": response,
            "query_embedding": get_embedding(query),
            "response_embedding": get_embedding(response)
        }
        add_memory_entry(character_file, new_entry)

        return response
    except Exception as e:
        logging.error(f"Error during OpenAI API call: {e}")
        return "I'm sorry, but I'm unable to process your request at this time."
