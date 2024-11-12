# textgen_llama.py
import subprocess
import os
import platform
import sqlite3
import logging
import sys
import signal

# Configure logging
logging.basicConfig(level=logging.INFO)

# Global variable to hold the Ollama server process
ollama_process = None


# Start Ollama server
def start_ollama_server():
    global ollama_process
    try:
        # If the user's OS is Windows
        if platform.system() == "Windows":
            # Start the Ollama server in a new process and store the process handle
            ollama_process = subprocess.Popen(["ollama", "serve"], shell=True)
        # If the user's OS is not Windows
        else:
            ollama_process = subprocess.Popen(["ollama", "serve"])
        logging.info("ollama server started successfully.")
    except Exception as e:
        logging.error(f"Failed to start ollama server: {e}")
        sys.exit(1)


# Function to stop Ollama server
def stop_ollama_server():
    global ollama_process
    try:
        if ollama_process and ollama_process.poll() is None:
            if platform.system() == "Windows":
                subprocess.call(
                    ["taskkill", "/F", "/T", "/PID", str(ollama_process.pid)]
                )
            else:
                ollama_process.terminate()
                try:
                    ollama_process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    ollama_process.kill()
            logging.info("ollama server stopped successfully.")
    except Exception as e:
        logging.error(f"Failed to stop ollama server: {e}")


# Configuration parameters
# Models to use for testing: llama3.1, llama3.2, llama2-uncensored
MODEL_COMMAND = ["ollama", "run", "llama3.1"]

# Base directory for character data
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CHARACTER_DATA_DIR = os.path.join(BASE_DIR, "../characterdata")
MEMORY_DB_DIR = os.path.join(BASE_DIR, "../memory_databases")

# Ensure memory database directory exists
if not os.path.exists(MEMORY_DB_DIR):
    os.makedirs(MEMORY_DB_DIR)


def get_db_path(character_file, model_name="ollama"):
    """Get the database path for a character and model."""
    return os.path.join(MEMORY_DB_DIR, f"{character_file}_{model_name}_memory.db")


# Initialize database for a character, but only if it doesn't already exist
def initialize_database(character_file, model_name="ollama"):
    db_path = get_db_path(character_file, model_name)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Check if the table already exists
    cursor.execute(
        """
        SELECT name FROM sqlite_master WHERE type='table' AND name='memory';
    """
    )

    if cursor.fetchone() is None:
        # Create table if it doesn't exist
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS memory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query TEXT NOT NULL,
                response TEXT NOT NULL,
                query_embedding BLOB,
                response_embedding BLOB
            )
        """
        )
        conn.commit()
        logging.info(
            f"Database initialized for character: {character_file} with model: {model_name}"
        )
    else:
        # Check if the required columns exist
        cursor.execute("PRAGMA table_info(memory);")
        columns = [info[1] for info in cursor.fetchall()]
        required_columns = {"query_embedding", "response_embedding"}
        missing_columns = required_columns - set(columns)
        if missing_columns:
            for column in missing_columns:
                cursor.execute(f"ALTER TABLE memory ADD COLUMN {column} BLOB;")
                logging.info(f"Added missing column '{column}' to the memory table.")
            conn.commit()
        else:
            logging.info(
                f"Database already exists and has all required columns for character: {character_file}"
            )

    conn.close()


# Function to add memory entry
def add_memory_entry(character_file, new_entry, model_name="ollama"):
    if (
        new_entry.get("query_embedding") is None
        or new_entry.get("response_embedding") is None
    ):
        logging.warning("Adding memory entry with None embeddings.")
        # Depending on requirements, you might skip adding such entries
        # For now, allow them to be None
    db_path = get_db_path(character_file, model_name)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO memory (query, response, query_embedding, response_embedding)
        VALUES (?, ?, ?, ?)
    """,
        (
            new_entry["query"],
            new_entry["response"],
            new_entry.get("query_embedding"),
            new_entry.get("response_embedding"),
        ),
    )
    conn.commit()
    conn.close()
    logging.info("New memory entry added.")


# Function to retrieve ALL past interactions
def get_all_memories(character_file, model_name="ollama"):
    db_path = get_db_path(character_file, model_name)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT query, response FROM memory")
    all_entries = cursor.fetchall()
    conn.close()

    memory_entries = []
    for entry_query, entry_response in all_entries:
        memory_entries.append(f"User: {entry_query}\nAssistant: {entry_response}")

    logging.info(f"Retrieved {len(memory_entries)} past interactions.")
    return memory_entries


# Main function to handle queries with full memory integration
def get_query(query, character_file, character_data, model_name="ollama"):
    # Initialize database if needed
    initialize_database(character_file, model_name)

    # Retrieve all past interactions
    memory_entries = get_all_memories(character_file, model_name)
    memory_context = "\n".join(memory_entries)

    # Prepare messages
    messages = (
        f"You must adhere to the following character information:\n{character_data}\n\n"
        f"Past Interactions:\n{memory_context}\n\n"
        f"Note: You should not respond with \"How may I assist you?\" or similar unless contextually appropriate.\n\n"
        f"Note: You are not to roleplay in responses. Do not under any circumstances use expressive actions such as *sigh* or *wipes brow*, as you are intended for conversational exchanges rather than roleplay.\n\n"
        f"User: {query}"
    )

    # Run the Llama model command, explicitly set encoding to 'utf-8'
    try:
        result = subprocess.run(
            MODEL_COMMAND,
            input=messages,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        if result.returncode != 0:
            raise RuntimeError(f"Error running model: {result.stderr}")

        response = result.stdout.strip()
        logging.info("Received response from Llama model.")

        # Update memory with the new interaction
        new_entry = {
            "query": query,
            "response": response,
            # Ollama does not provide embeddings, set them to None
            "query_embedding": None,
            "response_embedding": None,
        }
        add_memory_entry(character_file, new_entry, model_name)

        return response

    except Exception as e:
        logging.error(f"Error during model run: {e}")
        return "I'm sorry, but I'm unable to process your request at this time."