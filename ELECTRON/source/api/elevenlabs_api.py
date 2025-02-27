import logging
from typing import Optional
from elevenlabs import ElevenLabs
from keys_util import load_keys

# Configure logging to display debug messages
logging.basicConfig(level=logging.DEBUG)

# Load API keys from the keys.json file
keys = load_keys()
api_key = keys.get("ELEVENLABS_API_KEY", "")

# Check if the ElevenLabs API key is available
if not api_key:
    logging.warning("No ELEVENLABS_API_KEY found. ElevenLabs features will be disabled.")

# Initialize the ElevenLabs client only if we have an API key
client = ElevenLabs(api_key=api_key) if api_key else None

def convert_text_to_speech(voice_id: str, model_id: str, text: str) -> Optional[bytes]:
    """
    Convert text to speech using ElevenLabs.
    
    Args:
        voice_id (str): The ID of the voice to use.
        model_id (str): The ID of the model to use.
        text (str): The text to convert to speech.
        
    Returns:
        bytes: The audio data in bytes if successful, None otherwise.
    """
    if client is None:
        logging.error("ElevenLabs API key not configured. TTS not available.")
        return None

    try:
        # Convert text to speech using the ElevenLabs client
        response_audio_generator = client.text_to_speech.convert(
            voice_id=voice_id,
            model_id=model_id,
            text=text,
        )
        # Combine the audio data chunks into a single bytes object
        return b"".join(response_audio_generator)
    except Exception as e:
        logging.exception("Error during text-to-speech conversion:")
        return None
