# elevenlabs_api.py

import elevenlabs
from elevenlabs.client import ElevenLabs
import os
import json
import logging

from gui.api_key_manager import APIKeyManager

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize APIKeyManager
api_key_manager = APIKeyManager()

# Retrieve the ElevenLabs API key from keys.json
api_key = api_key_manager.get_api_key("elevenlabs")
if api_key:
    logging.info("ElevenLabs API Key found and loaded successfully.")
else:
    logging.warning(
        "ElevenLabs API Key not found. Please configure in keys.json to use ElevenLabs services."
    )

# Initialize ElevenLabs client
client_init = ElevenLabs(api_key=api_key)

# Load voice models from JSON file
VOICE_MODELS_FILE = os.path.join(
    os.path.dirname(__file__), "../persistent/elevenlabs_models.json"
)

# Initialize voice_models dictionary
voice_models = {}


def initialize_voice_models_file():
    try:
        if not os.path.exists(VOICE_MODELS_FILE):
            with open(VOICE_MODELS_FILE, "w", encoding="utf-8") as f:
                json.dump({}, f, indent=4)
            logging.info(f"Created new empty voice models file at {VOICE_MODELS_FILE}")
        return {}
    except Exception as e:
        logging.error(f"Error creating voice models file: {str(e)}")
        return {}


def load_voice_models():
    global voice_models
    try:
        with open(VOICE_MODELS_FILE, "r", encoding="utf-8-sig") as f:
            content = f.read().strip()
            if not content:
                voice_models_data = {}
                logging.warning(
                    f"{VOICE_MODELS_FILE} is empty. Initializing with no voice models."
                )
            else:
                voice_models_data = json.loads(content)
        if not isinstance(voice_models_data, dict):
            raise ValueError("Voice models JSON is not a dictionary.")
        voice_models = {
            name: elevenlabs.Voice(voice_id=vid)
            for name, vid in voice_models_data.items()
        }
        logging.info("Voice model JSON file loaded successfully.")
    except FileNotFoundError:
        logging.warning(f"{VOICE_MODELS_FILE} not found. Creating a new one.")
        with open(VOICE_MODELS_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f, indent=4)
        voice_models = {}
    except json.JSONDecodeError as e:
        logging.error(
            f"{VOICE_MODELS_FILE} is malformed: {str(e)}. Resetting to empty."
        )
        with open(VOICE_MODELS_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f, indent=4)
        voice_models = {}
    except Exception as e:
        logging.error(f"Unexpected error loading voice models: {str(e)}")
        voice_models = {}


def reload_voice_models():
    load_voice_models()


def add_voice_model(model_name, voice_id):
    try:
        # Load existing models
        voice_models_data = {}
        if os.path.exists(VOICE_MODELS_FILE):
            with open(VOICE_MODELS_FILE, "r", encoding="utf-8-sig") as f:
                content = f.read().strip()
                if not content:
                    voice_models_data = {}
                else:
                    voice_models_data = json.loads(content)

        # Check for duplicate model names
        if model_name in voice_models_data:
            logging.warning(
                f"Voice model '{model_name}' already exists. Overwriting its ID."
            )

        # Add or update the model
        voice_models_data[model_name] = voice_id

        # Save updated models
        with open(VOICE_MODELS_FILE, "w", encoding="utf-8") as f:
            json.dump(voice_models_data, f, indent=4, ensure_ascii=False)

        # Reload voice models
        load_voice_models()
        logging.info(f"Added/Updated voice model: {model_name}")
        return True
    except json.JSONDecodeError as e:
        logging.error(f"Failed to parse {VOICE_MODELS_FILE}: {str(e)}")
        return False
    except Exception as e:
        logging.error(f"Error adding voice model: {str(e)}")
        return False


def remove_voice_model(model_name):
    try:
        # Load existing models
        voice_models_data = {}
        if os.path.exists(VOICE_MODELS_FILE):
            with open(VOICE_MODELS_FILE, "r", encoding="utf-8-sig") as f:
                content = f.read().strip()
                if not content:
                    voice_models_data = {}
                else:
                    voice_models_data = json.loads(content)

        # Remove model if it exists
        if model_name in voice_models_data:
            del voice_models_data[model_name]

            # Save updated models
            with open(VOICE_MODELS_FILE, "w", encoding="utf-8") as f:
                json.dump(voice_models_data, f, indent=4, ensure_ascii=False)

            # Reload voice models
            load_voice_models()
            logging.info(f"Removed voice model: {model_name}")
            return True
        else:
            # logging.warning(f"Voice model '{model_name}' not found.")
            return False
    except json.JSONDecodeError as e:
        logging.error(f"Failed to parse {VOICE_MODELS_FILE}: {str(e)}")
        return False
    except Exception as e:
        logging.error(f"Error removing voice model: {str(e)}")
        return False


# Initialize current_voice_model as None
current_voice_model = None


def initialize_voice_models():
    load_voice_models()
    global current_voice_model
    # Set current_voice_model to the first model if available
    if voice_models:
        current_voice_model = next(
            iter(voice_models.values())
        )  # Get the first voice model
        logging.info(f"Default voice model set to: {next(iter(voice_models.keys()))}")


initialize_voice_models()


def change_voice_model(model_name):
    global current_voice_model
    if model_name in voice_models:
        current_voice_model = voice_models[model_name]
        logging.info(f"Voice model changed to: {model_name}")
    # else:
    # raise ValueError(f"Voice model '{model_name}' not found.")


def generate_audio(text):
    if current_voice_model is None:
        raise ValueError("No voice model selected. Please select a voice model first.")

    try:
        # Generate the audio using the current voice model's ID
        audio = client_init.generate(
            text=text,
            voice=current_voice_model.voice_id,
            model="eleven_multilingual_v2",
        )
        # Convert the stream (generator) to bytes
        audio_bytes = b"".join(audio)
        return audio_bytes
    except Exception as e:
        logging.error(f"Error generating audio: {str(e)}")
        raise


def get_available_voice_models():
    return list(voice_models.keys())
