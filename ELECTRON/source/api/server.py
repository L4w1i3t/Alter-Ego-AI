import base64
import json
import os
import logging
import platform
import sys
from flask import Flask, request, jsonify
from waitress import serve
from datetime import datetime, timezone
# We add the current directory to sys.path so we can import local modules (like emotions_api, keys_util, etc.).
sys.path.append(os.path.dirname(__file__))

# Local imports
from emotions_api import detect_emotions
from elevenlabs_api import convert_text_to_speech
from memory_manager import (
    get_stm_for_persona,
    get_embedder_for_persona,
    add_to_longterm_memory,
    append_chat_message,
    clear_memory
)
from ollama_manager import start_server, stop_server, query_ollama
from openai_manager import query_openai, warmup_openai

# Ensure current directory is in sys.path
sys.path.append(os.path.dirname(__file__))

# Flask App Setup
app = Flask(__name__)
logging.basicConfig(level=logging.DEBUG)

# Determine backend mode
mode = os.environ.get("MODEL_BACKEND", "ollama")
openai_enabled = True if mode == "openai" else False

@app.route("/clear_stm", methods=["POST"])
def clear_stm():
    clear_memory()
    return "OK", 200

@app.route("/stop", methods=["POST"])
def stop():
    stop_server()
    shutdown_server = request.environ.get("werkzeug.server.shutdown")
    if shutdown_server is not None:
        shutdown_server()
    return '', 204

@app.route("/query", methods=["POST"])
def query():
    data = request.get_json()
    user_query = data.get("query", "")
    persona_name = data.get("persona_name", "ALTER EGO")
    persona_prompt = data.get("persona_prompt", "You are a program called ALTER EGO.")
    voice_model_name = data.get("voice_model_name", None)

    if not user_query or not isinstance(user_query, str):
        return jsonify({"error": "Invalid query"}), 400
    if not persona_prompt or not isinstance(persona_prompt, str):
        return jsonify({"error": "Invalid persona prompt"}), 400

    # Warm-up logic
    if user_query.strip().lower() == "warm-up":
        if mode == "ollama":
            final_prompt = "User: warm-up\nAssistant:"
            answer = query_ollama(final_prompt, persona_content=persona_prompt)
        else:
            answer = warmup_openai()
        return jsonify({
            "response": "(Warming up complete)",
            "query_emotions": {},
            "response_emotions": {},
            "audio_base64": None
        })

    # Retrieve short-term memory
    stm_buffer = get_stm_for_persona(persona_name)

    # Retrieve long-term memory
    embedder = get_embedder_for_persona(persona_name)
    top_k = 2
    ltm_results = embedder.search(user_query, top_k=top_k)
    relevant_context = ""
    for (chunk_text, dist) in ltm_results:
        relevant_context += f"{chunk_text}\n"

    # Query using Ollama
    if mode == "ollama":
        recent_exchanges = stm_buffer[-6:] if len(stm_buffer) >= 6 else stm_buffer
        memory_text = ""
        for entry in recent_exchanges:
            if entry["role"] == "user":
                memory_text += f"User: {entry['content']}\n"
            else:
                memory_text += f"Assistant: {entry['content']}\n"
        final_prompt = (
            f"Relevant Memory:\n{relevant_context}\n"
            f"{memory_text}"
            f"User: {user_query}\nAssistant:"
        )
        answer = query_ollama(final_prompt, persona_content=persona_prompt)
        if answer.startswith("Error:"):
            return jsonify({"error": answer}), 400
        stm_buffer.append({"role": "user", "content": user_query})
        stm_buffer.append({"role": "assistant", "content": answer})
        while len(stm_buffer) > 10:
            stm_buffer.pop(0)
        add_to_longterm_memory(user_query, answer, persona_name)
    
    # Query using OpenAI
    elif mode == "openai" and openai_enabled:
        answer = query_openai(user_query, persona_prompt, stm_buffer, relevant_context)
        stm_buffer.append({"role": "user", "content": user_query})
        stm_buffer.append({"role": "assistant", "content": answer})
        while len(stm_buffer) > 10:
            stm_buffer.pop(0)
        add_to_longterm_memory(user_query, answer, persona_name)
    else:
        return jsonify({"error": "Backend not supported"}), 400

    # Emotion Detection
    query_emotions_list = detect_emotions([user_query])
    response_emotions_list = detect_emotions([answer])
    query_emotions = query_emotions_list[0] if query_emotions_list else {}
    response_emotions = response_emotions_list[0] if response_emotions_list else {}

    # TTS
    models_path = os.path.join(os.path.dirname(__file__), "../persistentdata/elevenlabs_models.json")
    try:
        with open(models_path, "r", encoding="utf-8") as f:
            voice_models = json.load(f)
    except Exception as e:
        logging.error(f"Error reading elevenlabs_models.json: {e}")
        voice_models = {}
    audio_base64 = None
    if voice_model_name and voice_model_name in voice_models:
        voice_id = voice_models[voice_model_name]
        model_id = "eleven_multilingual_v2"
        response_audio = convert_text_to_speech(voice_id, model_id, answer)
        if response_audio:
            audio_base64 = base64.b64encode(response_audio).decode("utf-8")

    append_chat_message(persona_name, "user", user_query)
    append_chat_message(persona_name, "assistant", answer)

    return jsonify({
        "response": answer,
        "query_emotions": query_emotions,
        "response_emotions": response_emotions,
        "audio_base64": audio_base64,
    })

if __name__ == "__main__":
    if mode == "ollama":
        start_server()
    print("Starting production server on http://127.0.0.1:5000")
    serve(app, host="127.0.0.1", port=5000)
