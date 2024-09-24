# elevenlabs_api.py
import elevenlabs
from elevenlabs.client import ElevenLabs
import os
import dotenv
import json

# Load environment variables
dotenv.load_dotenv()

api_key = os.getenv("ELEVENLABS_API_KEY")
if not api_key:
    exit("No ElevenLabs API Key found.")
print("ElevenLabs API Key loaded successfully.")

# init
client_init = ElevenLabs(
    api_key=api_key,
)

# Load voice models from JSON file
VOICE_MODELS_FILE = os.path.join(os.path.dirname(__file__), 'elevenlabs_models.json')

try:
    with open(VOICE_MODELS_FILE, 'r') as f:
        voice_models_data = json.load(f)
        # Convert the JSON data into a dictionary of Voice objects
        voice_models = {}
        for model_name, voice_id in voice_models_data.items():
            voice_models[model_name] = elevenlabs.Voice(voice_id=voice_id)
except FileNotFoundError:
    exit(f"Voice models file '{VOICE_MODELS_FILE}' not found.")
except json.JSONDecodeError as e:
    exit(f"Error parsing JSON file '{VOICE_MODELS_FILE}': {str(e)}")

# Set a default voice model
current_voice_model = voice_models["Aigis (DEFAULT)"]

def change_voice_model(model_name):
    global current_voice_model
    if model_name in voice_models:
        current_voice_model = voice_models[model_name]
    else:
        raise ValueError(f"Voice model '{model_name}' not found.")

def generate_audio(text):
    try:
        # Generate the audio using the current voice model
        audio = client_init.generate(
            text=text,
            voice=current_voice_model,
            model="eleven_multilingual_v2"
        )
        # Convert the stream (generator) to bytes
        audio_bytes = b"".join(audio)
        return audio_bytes
    except Exception as e:
        print(f"Error generating audio: {str(e)}")
        raise