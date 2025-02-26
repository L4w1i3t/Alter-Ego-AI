import os
import json
import logging
from datetime import datetime, timezone
from embedding_memory import EmbeddingMemory

# Global variables for STM and LTM
STM_BUFFERS = {}
MAX_BUFFER_SIZE = 10
EMBEDDING_MEMORIES = {}

def get_stm_for_persona(persona_name):
    if persona_name not in STM_BUFFERS:
        STM_BUFFERS[persona_name] = []
    return STM_BUFFERS[persona_name]

def get_embedder_for_persona(persona_name):
    if persona_name not in EMBEDDING_MEMORIES:
        EMBEDDING_MEMORIES[persona_name] = EmbeddingMemory(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            persona_name=persona_name
        )
    return EMBEDDING_MEMORIES[persona_name]

def add_to_longterm_memory(user_text, assistant_text, persona_name):
    embedder = get_embedder_for_persona(persona_name)
    user_chunk = f"User said: {user_text}"
    assistant_chunk = f"Assistant replied: {assistant_text}"
    embedder.add_text(user_chunk)
    embedder.add_text(assistant_chunk)

def get_chat_history_path(persona_name):
    base_dir = os.path.join(
        os.path.dirname(__file__),
        "..",
        "persistentdata",
        "memory_databases",
        persona_name
    )
    if not os.path.exists(base_dir):
        os.makedirs(base_dir, exist_ok=True)
    return os.path.join(base_dir, "chat_history.json")

def load_chat_history(persona_name):
    file_path = get_chat_history_path(persona_name)
    if not os.path.exists(file_path):
        return []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        logging.warning(f"[{persona_name}] chat_history.json corrupted. Returning empty.")
        return []

def save_chat_history(persona_name, history_array):
    file_path = get_chat_history_path(persona_name)
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(history_array, f, indent=2)

def append_chat_message(persona_name, role, content):
    history = load_chat_history(persona_name)
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "role": role,
        "content": content
    }
    history.append(entry)
    save_chat_history(persona_name, history)

def clear_memory():
    global STM_BUFFERS, EMBEDDING_MEMORIES
    STM_BUFFERS = {}
    EMBEDDING_MEMORIES = {}
    logging.info("Short-term memory and in-memory embedding memories have been cleared.")
