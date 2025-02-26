import os
import json
import logging
from datetime import datetime, timezone

# COMPATIBILITY NOTE: These functions are retained for compatibility with 
# the JavaScript front-end that expects chat_history.json files.
# New code should use SQLMemory directly.

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