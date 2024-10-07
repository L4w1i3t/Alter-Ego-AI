# local_llm.py
import os
import sqlite3
import pickle
import logging
from sklearn.metrics.pairwise import cosine_similarity
import configparser

from dotenv import load_dotenv
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch
from sentence_transformers import SentenceTransformer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("alter_ego.log"),
        logging.StreamHandler()
    ]
)

# Load environment variables
load_dotenv()

# Load configuration
config = configparser.ConfigParser()
config.read(os.path.join(os.path.dirname(__file__), '../config.ini'))

# Configuration parameters
# ------------------------
# Model paths
GPT_J_MODEL_NAME = config.get('LocalLLM', 'gpt_j_model', fallback='EleutherAI/gpt-j-6B')
EMBEDDING_MODEL_NAME = config.get('LocalLLM', 'embedding_model', fallback='sentence-transformers/all-MiniLM-L6-v2')

# Token limits
# ------------
MAX_TOTAL_TOKENS = config.getint('LocalLLM', 'max_total_tokens', fallback=1200)
MAX_RESPONSE_TOKENS = config.getint('LocalLLM', 'max_response_tokens', fallback=200)
MAX_CONTEXT_TOKENS = MAX_TOTAL_TOKENS - MAX_RESPONSE_TOKENS

# Memory parameters
TOP_K = config.getint('Memory', 'top_k', fallback=3)
MAX_SHORT_TERM_MEMORY = config.getint('Memory', 'max_short_term_memory', fallback=5)

# Base directory for character data
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CHARACTER_DATA_DIR = os.path.join(BASE_DIR, "../characterdata")
MEMORY_DB_DIR = os.path.join(BASE_DIR, "../memory_databases")

# Ensure memory database directory exists
if not os.path.exists(MEMORY_DB_DIR):
    os.makedirs(MEMORY_DB_DIR)

# Check if GPU is available
use_gpu = torch.cuda.is_available()
device = torch.device("cuda" if use_gpu else "cpu")
logging.info(f"Using device: {device}")

# Load GPT-J-6B with optimizations
try:
    logging.info(f"Loading model: {GPT_J_MODEL_NAME}")
    if use_gpu:
        model = AutoModelForCausalLM.from_pretrained(
            GPT_J_MODEL_NAME,
            load_in_8bit=True,                  # Enable 8-bit loading
            device_map='auto',                  # Automatically map to available devices
            torch_dtype=torch.float16,          # Use mixed precision
            low_cpu_mem_usage=True               # Optimize CPU memory usage
        )
        logging.info("GPT-J-6B model loaded successfully with 8-bit quantization on GPU.")
    else:
        model = AutoModelForCausalLM.from_pretrained(
            GPT_J_MODEL_NAME,
            device_map='cpu',
            torch_dtype=torch.float16
        )
        logging.warning("GPU not detected. Loaded GPT-J-6B model on CPU without quantization.")
except RuntimeError as e:
    logging.error(f"RuntimeError during model loading: {e}")
    logging.warning("Attempting to load the model without quantization on CPU.")
    try:
        model = AutoModelForCausalLM.from_pretrained(
            GPT_J_MODEL_NAME,
            device_map='cpu',
            torch_dtype=torch.float16
        )
        logging.info("GPT-J-6B model loaded successfully on CPU without quantization.")
    except Exception as ex:
        logging.critical(f"Failed to load GPT-J-6B model: {ex}")
        raise ex

# Load tokenizer
try:
    tokenizer = AutoTokenizer.from_pretrained(GPT_J_MODEL_NAME)
    logging.info("Tokenizer loaded successfully.")
except Exception as e:
    logging.error(f"Error loading tokenizer: {e}")
    raise e

# Load Embedding Model
try:
    logging.info(f"Loading embedding model: {EMBEDDING_MODEL_NAME}")
    embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME)
    logging.info("Embedding model loaded successfully.")
except Exception as e:
    logging.error(f"Error loading embedding model: {e}")
    raise e

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

# Function to get embeddings using the local embedding model
def get_embedding(text):
    embedding = embedding_model.encode(text)
    return embedding.tolist()  # Convert to list for storage

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

    # Generate a summary using GPT-J-6B
    summary_prompt = f"Summarize the following interactions to help you remember important details for future conversations:\n\n{long_term_text}\n\nSummary:"
    max_summary_tokens = 150  # Adjust based on needs

    try:
        summary = generate_response(summary_prompt)
        logging.info("Long-term memory summarized.")
        return summary
    except Exception as e:
        logging.error(f"Error during memory summarization: {e}")
        return "Could not summarize long-term memory."

# Function to generate responses using GPT-J-6B
def generate_response(prompt):
    try:
        inputs = tokenizer(prompt, return_tensors='pt').to(device)
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=MAX_RESPONSE_TOKENS,
                temperature=0.7,
                top_p=0.95,
                top_k=60,
                do_sample=True,
                pad_token_id=tokenizer.eos_token_id
            )
        response = tokenizer.decode(outputs[0], skip_special_tokens=True)
        return response
    except Exception as e:
        logging.error(f"Error during model inference: {e}")
        raise e

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

    # Prepare the full prompt
    system_instructions = f"Your responses fully adhere to the following character information:\n{character_data}\n"
    system_instructions += f"Long-term Memory Summary:\n{long_term_summary}\n"
    system_instructions += f"Relevant Previous Interactions:\n{memory_context}\n"
    system_instructions += f"General rule to follow: NEVER end responses with \"How can I assist you?\" or similar.\n"
    user_input = f"User: {query}\nAssistant:"

    full_prompt = system_instructions + user_input

    # Token counting using tokenizer
    enc = tokenizer
    total_tokens = len(enc.encode(full_prompt))

    # Log the number of tokens used before adjustments
    logging.info(f"Total tokens used before adjustments: {total_tokens}")

    # Adjust context if total tokens exceed the maximum allowed
    if total_tokens > MAX_CONTEXT_TOKENS:
        logging.warning(f"Token limit exceeded. Total tokens: {total_tokens}, Max allowed: {MAX_CONTEXT_TOKENS}")
        # Remove the least relevant memory entries
        while total_tokens > MAX_CONTEXT_TOKENS and relevant_memories:
            relevant_memories.pop()
            memory_entries = [f"User: {entry['query']}\nAssistant: {entry['response']}" for entry in relevant_memories]
            memory_context = "\n".join(memory_entries)
            system_instructions = f"Your responses fully adhere to the following character information:\n{character_data}\n"
            system_instructions += f"Long-term Memory Summary:\n{long_term_summary}\n"
            system_instructions += f"Relevant Previous Interactions:\n{memory_context}\n"
            system_instructions += f"General rule to follow: NEVER end responses with \"How can I assist you?\" or similar.\n"
            user_input = f"User: {query}\nAssistant:"

            full_prompt = system_instructions + user_input
            total_tokens = len(enc.encode(full_prompt))
            logging.info(f"Tokens after memory adjustment: {total_tokens}")

        if total_tokens > MAX_CONTEXT_TOKENS:
            # As a last resort, remove the long-term memory summary
            logging.warning("Still over token limit after removing memories, removing long-term memory summary.")
            system_instructions = f"Your responses fully adhere to the following character information:\n{character_data}\n"
            system_instructions += f"Relevant Previous Interactions:\n{memory_context}\n"
            system_instructions += f"General rule to follow: NEVER end responses with \"How can I assist you?\" or similar.\n"
            full_prompt = system_instructions + user_input
            total_tokens = len(enc.encode(full_prompt))
            logging.info(f"Tokens after removing long-term memory summary: {total_tokens}")

            if total_tokens > MAX_CONTEXT_TOKENS:
                logging.error("Unable to adjust context within token limits.")
                return "I'm sorry, but I'm unable to process your request due to context length limitations."

    # Log the final token count before making the API call
    logging.info(f"Final token count before API call: {total_tokens}")

    # Generate response using local GPT-J-6B
    try:
        response = generate_response(full_prompt)
        logging.info("Received response from GPT-J-6B model.")

        # Log the number of tokens used in the response
        response_tokens = len(enc.encode(response))
        logging.info(f"Tokens used in the response: {response_tokens}")

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
        logging.error(f"Error during model inference: {e}")
        return "I'm sorry, but I'm unable to process your request at this time."
