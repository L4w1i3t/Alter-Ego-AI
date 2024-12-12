import logging
import json
from elevenlabs import ElevenLabs

# Set up logging
logging.basicConfig(level=logging.DEBUG)

# Load the API key
keys_file = "../persistentdata/keys.json"
try:
    with open(keys_file, "r") as file:
        keys = json.load(file)
        api_key = keys.get("ELEVENLABS_API_KEY")
        if not api_key:
            raise ValueError("ELEVENLABS_API_KEY is missing in keys.json.")
except FileNotFoundError:
    logging.error(f"Keys file not found: {keys_file}")
    raise
except json.JSONDecodeError:
    logging.error(f"Error decoding JSON from {keys_file}")
    raise
except Exception as e:
    logging.error(f"Error loading API key: {e}")
    raise

# Initialize the ElevenLabs client
logging.debug(f"Initializing ElevenLabs client with API key: {api_key}")
client = ElevenLabs(api_key=api_key)