from flask import Flask, request, jsonify
from openai_api import get_response
from emotions_api import detect_emotions
import base64
import json
import os
import logging

from elevenlabs_api import client

app = Flask(__name__)

@app.route('/query', methods=['POST'])
def query():
    data = request.get_json()
    user_query = data.get("query", "")
    persona_prompt = data.get("persona_prompt", "You are a program called ALTER EGO.")
    voice_model_name = data.get("voice_model_name", None)  # This could be None or empty, whichever works

    # Get the response from OpenAI
    answer = get_response(user_query, system_prompt=persona_prompt)

    # Detect emotions
    query_emotions_list = detect_emotions([user_query])
    response_emotions_list = detect_emotions([answer])

    query_emotions = query_emotions_list[0] if query_emotions_list else {}
    response_emotions = response_emotions_list[0] if response_emotions_list else {}

    # Load voice models
    models_path = os.path.join(os.path.dirname(__file__), '../persistentdata/elevenlabs_models.json')
    try:
        with open(models_path, 'r', encoding='utf-8') as f:
            voice_models = json.load(f)
    except Exception as e:
        logging.error(f"Error reading elevenlabs_models.json: {e}")
        voice_models = {}

    audio_base64 = None

    # Only proceed with TTS if a voice_model_name is provided and is found in the models
    if voice_model_name and voice_model_name in voice_models:
        voice_id = voice_models[voice_model_name]
        model_id = "eleven_multilingual_v2"

        try:
            # `response_audio` here might be a generator of audio chunks
            response_audio_generator = client.text_to_speech.convert(
                voice_id=voice_id,
                model_id=model_id,
                text=answer,
            )

            # Join all chunks into one bytes object
            response_audio = b''.join(response_audio_generator)

            audio_base64 = base64.b64encode(response_audio).decode('utf-8')
        except Exception as e:
            logging.error(f"An error occurred during text-to-speech conversion: {e}")
            audio_base64 = None

    return jsonify({
        "response": answer,
        "query_emotions": query_emotions,
        "response_emotions": response_emotions,
        "audio_base64": audio_base64
    })


if __name__ == "__main__":
    app.run(port=5000)