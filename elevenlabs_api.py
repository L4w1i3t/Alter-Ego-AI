# elevenlabs_api.py
import elevenlabs
import os
import dotenv

# Load environment variables
dotenv.load_dotenv()

elevenlabs_api_key = os.getenv('ELEVENLABS_API_KEY')
if not elevenlabs_api_key:
    exit("No Elevenlabs API Key found.")
print("Elevenlabs API Key loaded successfully.")
elevenlabs.set_api_key(elevenlabs_api_key)

# Load and initiate a voice model and its settings
voice = elevenlabs.Voice(
    voice_id="oFxovaqXut8XX19I4UGi",
    settings=elevenlabs.VoiceSettings(
        stability = 0.5,
        similarity_boost = 0.75
    )
)

def generate_audio(text):
    # Generate the audio using the Elevenlabs API
    audio = elevenlabs.generate(
        text=text,
        voice=voice,
        model="eleven_multilingual_v2"
    )
    return audio