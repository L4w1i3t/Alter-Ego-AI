import os
import json
import logging

# Configure logging to display debug messages
logging.basicConfig(level=logging.DEBUG)

def load_keys():
    """
    Load API keys from the keys.json file.
    If the file or required keys are missing, create them with default values.
    Returns:
        dict: A dictionary containing the API keys.
    """
    keys_path = os.path.join(os.path.dirname(__file__), "../persistentdata/keys.json")

    # Ensure the directory exists
    keys_dir = os.path.dirname(keys_path)
    if not os.path.exists(keys_dir):
        os.makedirs(keys_dir, exist_ok=True)

    # If keys.json doesn't exist, create it with empty defaults
    if not os.path.exists(keys_path):
        default_keys = {"OPENAI_API_KEY": "", "ELEVENLABS_API_KEY": ""}
        with open(keys_path, "w", encoding="utf-8") as f:
            json.dump(default_keys, f, indent=4)

    # Load keys and handle corruption or missing entries
    try:
        with open(keys_path, "r", encoding="utf-8") as f:
            keys = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        logging.warning(
            "keys.json is missing or corrupted. Recreating with empty defaults."
        )
        keys = {"OPENAI_API_KEY": "", "ELEVENLABS_API_KEY": ""}
        with open(keys_path, "w", encoding="utf-8") as f:
            json.dump(keys, f, indent=4)
        return keys

    # Ensure required keys exist
    changed = False
    if "OPENAI_API_KEY" not in keys:
        keys["OPENAI_API_KEY"] = ""
        changed = True
    if "ELEVENLABS_API_KEY" not in keys:
        keys["ELEVENLABS_API_KEY"] = ""
        changed = True

    # Save back if we added missing keys
    if changed:
        with open(keys_path, "w", encoding="utf-8") as f:
            json.dump(keys, f, indent=4)

    return keys