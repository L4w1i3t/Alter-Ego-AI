# elevenlabs_api.py
import elevenlabs
from elevenlabs.client import ElevenLabs
import os
import dotenv

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

# Available voice models
voice_models = {
    "Yukari Takeba (DEFAULT)": elevenlabs.Voice(voice_id="oFxovaqXut8XX19I4UGi"),
    "Yukari Takeba (ORIGINAL)": elevenlabs.Voice(voice_id="r9KOIKrF66IfRxj8R8hN"),
    "My roommate David": elevenlabs.Voice(voice_id="RaLB9SP9w3NGygxqOomT"),
}

# Set a default voice model
current_voice_model = voice_models["Yukari Takeba (DEFAULT)"]

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