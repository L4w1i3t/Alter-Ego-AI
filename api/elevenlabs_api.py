import elevenlabs
from elevenlabs.client import ElevenLabs
import os
import dotenv
import sys

# Load environment variables
dotenv.load_dotenv()

# Get the API key from environment variables
api_key = os.getenv("ELEVENLABS_API_KEY")

# Check if the API key is found, if not, exit with an error message
if not api_key:
    exit("No ElevenLabs API Key found.")
print("ElevenLabs API Key loaded successfully.")

# Initialize the ElevenLabs client
client_init = ElevenLabs(
    api_key=api_key,
)

# Load and initiate a voice model and its settings
voice_model = elevenlabs.Voice(
    voice_id="oFxovaqXut8XX19I4UGi",
    settings=elevenlabs.VoiceSettings(
        stability=0.5,
        similarity_boost=0.75
    )
)

def generate_audio(text):
    global voice
    try:
        # Generate the audio using the Elevenlabs API
        audio = client_init.generate(
            text=text,
            voice=voice_model,
            model="eleven_multilingual_v2"
        )
        # Convert the stream (generator) to bytes
        audio_bytes = b"".join(audio)
        return audio_bytes
    except Exception as e:
        print(f"Error generating audio: {str(e)}")
        raise
