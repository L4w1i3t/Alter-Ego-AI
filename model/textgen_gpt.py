# textgen_gpt.py
import openai
import os
import sqlite3
import pickle
from sklearn.metrics.pairwise import cosine_similarity
from tiktoken import encoding_for_model
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

# Load environment variables
from dotenv import load_dotenv

load_dotenv()

openai_api_key = os.getenv("OPENAI_API_KEY")
if openai_api_key:
    logging.info("OpenAI API Key found and loaded successfully.")
else:
    logging.warning("OpenAI API Key not found. Please configure in settings to use OpenAI services.")
openai.api_key = openai_api_key

# Configuration parameters
# ------------------------
# OpenAI models
MODEL = "gpt-4o-2024-08-06"
SUMMARIZATION_MODEL = "gpt-4o"
EMBEDDING_MODEL = "text-embedding-ada-002"

# Token limits
# ------------
# Maximum total tokens allowed for the request (including context and response)
MAX_TOTAL_TOKENS = 1000

# Maximum tokens to reserve for the assistant's response
MAX_RESPONSE_TOKENS = 200

# Maximum tokens allowed for the context (excluding the response)
MAX_CONTEXT_TOKENS = MAX_TOTAL_TOKENS - MAX_RESPONSE_TOKENS

# Memory parameters
TOP_K = 3
MAX_SHORT_TERM_MEMORY = 5

# Base directory for character data
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CHARACTER_DATA_DIR = os.path.join(BASE_DIR, "../characterdata")
MEMORY_DB_DIR = os.path.join(BASE_DIR, "../memory_databases")

# Ensure memory database directory exists
if not os.path.exists(MEMORY_DB_DIR):
    os.makedirs(MEMORY_DB_DIR)


def get_db_path(character_file, model_name="gpt"):
    """Get the database path for a character and model."""
    return os.path.join(MEMORY_DB_DIR, f"{character_file}_{model_name}_memory.db")


# Initialize database for a character
def initialize_database(character_file, model_name="gpt"):
    db_path = get_db_path(character_file, model_name)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
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
    conn.close()
    logging.info(
        f"Database initialized for character: {character_file} with model: {model_name}"
    )


# Function to get embeddings
def get_embedding(text):
    response = openai.embeddings.create(input=text, model=EMBEDDING_MODEL)
    embedding = response.data[0].embedding
    return embedding


# Function to add memory entry
def add_memory_entry(character_file, new_entry, model_name="gpt"):
    if new_entry["query_embedding"] is None or new_entry["response_embedding"] is None:
        logging.error("Cannot add memory entry with None embeddings.")
        return  # Or handle accordingly

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
            pickle.dumps(new_entry["query_embedding"]),
            pickle.dumps(new_entry["response_embedding"]),
        ),
    )
    conn.commit()
    conn.close()
    logging.info("New memory entry added.")


# Function to retrieve relevant memories using embeddings
def get_relevant_memories(character_file, query, model_name="gpt", top_k=TOP_K):
    query_embedding = get_embedding(query)
    db_path = get_db_path(character_file, model_name)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT query, response, query_embedding FROM memory")
    all_entries = cursor.fetchall()
    conn.close()
    similarities = []
    for entry_query, entry_response, entry_query_embedding_pickle in all_entries:
        if entry_query_embedding_pickle is None:
            logging.warning(
                f"Skipping entry with None embedding: Query='{entry_query}'"
            )
            continue  # Skip this entry
        try:
            entry_query_embedding = pickle.loads(entry_query_embedding_pickle)
        except (pickle.UnpicklingError, TypeError) as e:
            logging.error(
                f"Failed to deserialize embedding for query '{entry_query}': {e}"
            )
            continue  # Skip this entry

        sim = cosine_similarity([query_embedding], [entry_query_embedding])[0][0]
        similarities.append((sim, {"query": entry_query, "response": entry_response}))
    similarities.sort(key=lambda x: x[0], reverse=True)
    relevant_entries = [entry for _, entry in similarities[:top_k]]
    logging.info(f"Retrieved {len(relevant_entries)} relevant memories.")
    return relevant_entries


# Function to summarize long-term memory
def summarize_memory(character_file, model_name="gpt"):
    db_path = get_db_path(character_file, model_name)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT query, response FROM memory")
    all_entries = cursor.fetchall()
    conn.close()
    long_term_entries = [
        f"User: {entry_query}\nAssistant: {entry_response}"
        for entry_query, entry_response in all_entries
    ]
    long_term_text = "\n".join(long_term_entries)
    if not long_term_text.strip():
        return "No previous interactions to summarize."
    # Generate a summary before applying to context
    summary_prompt = f"Summarize the following interactions to help you remember important details for future conversations:\n\n{long_term_text}"
    max_summary_tokens = 150  # Adjust based on needs
    try:
        summary_response = openai.chat.completions.create(
            model=SUMMARIZATION_MODEL,
            messages=[{"role": "user", "content": summary_prompt}],
            max_tokens=max_summary_tokens,
            temperature=0.7,
        )
        summary = summary_response.choices[0].message.content.strip()
        logging.info("Long-term memory summarized.")
        return summary
    except Exception as e:
        logging.error(f"Error during memory summarization: {e}")
        return "Could not summarize long-term memory."


# Main function to handle queries with character memory integration
def get_query(query, character_file, character_data, model_name="gpt"):
    # Initialize database if needed
    initialize_database(character_file, model_name)

    # Retrieve relevant memories
    relevant_memories = get_relevant_memories(character_file, query, model_name)

    # Prepare memory context
    memory_entries = [
        f"User: {entry['query']}\nAssistant: {entry['response']}"
        for entry in relevant_memories
    ]
    memory_context = "\n".join(memory_entries)

    # Summarize long-term memory
    long_term_summary = summarize_memory(character_file, model_name)

    # Prepare messages
    messages = [
        {
            "role": "system",
            "content": f"Your responses fully adhere to the following character information:\n{character_data}",
        },
        {
            "role": "system",
            "content": f"Long-term Memory Summary:\n{long_term_summary}",
        },
        {
            "role": "assistant",
            "content": f"Relevant Previous Interactions:\n{memory_context}",
        },
        {
            "role": "system",
            "content": 'General rules to follow: NEVER end responses with "How can I assist you?" or similar, you are not to roleplay in responses. Avoid using expressive actions such as *sigh* or *wipes brow*, as you are intended for conversational exchanges rather than roleplay.',
        },
        {"role": "user", "content": query},
    ]

    # Token counting
    enc = encoding_for_model(MODEL)
    total_tokens = sum(len(enc.encode(message["content"])) for message in messages)

    # Print the number of tokens used before sending the API call
    print(f"Total tokens used before adjustments: {total_tokens}")

    # Adjust context if total tokens exceed the maximum allowed
    if total_tokens > MAX_CONTEXT_TOKENS:
        print(
            f"Token limit exceeded. Total tokens: {total_tokens}, Max allowed: {MAX_CONTEXT_TOKENS}"
        )
        # Remove the least relevant memory entries
        logging.warning(
            "Token limit exceeded, adjusting context by removing least relevant memories."
        )
        while total_tokens > MAX_CONTEXT_TOKENS and relevant_memories:
            relevant_memories.pop()
            memory_entries = [
                f"User: {entry['query']}\nAssistant: {entry['response']}"
                for entry in relevant_memories
            ]
            memory_context = "\n".join(memory_entries)
            messages[2][
                "content"
            ] = f"Relevant Previous Interactions:\n{memory_context}"
            total_tokens = sum(
                len(enc.encode(message["content"])) for message in messages
            )

            # Print the number of tokens after removing memories
            print(f"Tokens after memory adjustment: {total_tokens}")

        if total_tokens > MAX_CONTEXT_TOKENS:
            # As a last resort, remove the long-term memory summary
            logging.warning(
                "Still over token limit after removing memories, removing long-term memory summary."
            )
            messages.pop(1)
            total_tokens = sum(
                len(enc.encode(message["content"])) for message in messages
            )

            # Print the number of tokens after removing long-term memory summary
            print(f"Tokens after removing long-term memory summary: {total_tokens}")

            if total_tokens > MAX_CONTEXT_TOKENS:
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
            temperature=0.7,
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
            "response_embedding": get_embedding(response),
        }
        add_memory_entry(character_file, new_entry, model_name)

        return response
    except Exception as e:
        logging.error(f"Error during OpenAI API call: {e}")
        return "I'm sorry, but I'm unable to process your request at this time."
