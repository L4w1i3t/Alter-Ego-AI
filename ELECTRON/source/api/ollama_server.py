from flask import Flask, request, jsonify
import base64
import json
import os
import logging
import platform
import subprocess
import sys
from waitress import serve

sys.path.append(os.path.dirname(__file__))
from emotions_api import detect_emotions
from elevenlabs_api import convert_text_to_speech

app = Flask(__name__)

# Configure logging to display debug messages
logging.basicConfig(level=logging.DEBUG)

# Determine backend from environment variable
mode = os.environ.get("MODEL_BACKEND", "ollama")

# Global variable to hold the Ollama server process
ollama_process = None

def start_ollama_server():
    """
    Start the Ollama server process.
    """
    global ollama_process
    try:
        ollama_exe_path = os.path.join(os.path.dirname(__file__), "Ollama/ollama.exe")
        if platform.system() == "Windows":
            # Use creationflags so that Ollama is the direct child in a new process group
            creationflags = subprocess.CREATE_NEW_PROCESS_GROUP
            ollama_process = subprocess.Popen(
                [ollama_exe_path, "serve"], shell=False, creationflags=creationflags
            )
        else:
            ollama_process = subprocess.Popen([ollama_exe_path, "serve"])
        logging.info("Ollama server started successfully.")
    except Exception as e:
        logging.error(f"Failed to start Ollama server: {e}")
        sys.exit(1)

def stop_ollama_server():
    """
    Stop the Ollama server process.
    """
    global ollama_process
    try:
        if ollama_process and ollama_process.poll() is None:
            if platform.system() == "Windows":
                # First try to kill the process by PID
                subprocess.call(["taskkill", "/F", "/T", "/PID", str(ollama_process.pid)])
                # Last resort: forcibly kill by name
                subprocess.call(["taskkill", "/F", "/IM", "ollama.exe"])
                subprocess.call(["taskkill", "/F", "/IM", "ollama_llama_server.exe"])
            else:
                ollama_process.terminate()
                ollama_process.wait(timeout=5)
            logging.info("Ollama server stopped successfully.")
    except Exception as e:
        logging.error(f"Failed to stop Ollama server: {e}")

@app.route("/stop", methods=["POST"])
def stop():
    """
    Endpoint to stop the Ollama server and Flask application.
    """
    stop_ollama_server()

    # Tell Flask/Werkzeug to shut down (if running via Werkzeug)
    shutdown_server = request.environ.get("werkzeug.server.shutdown")
    if shutdown_server is not None:
        shutdown_server()
    return '', 204

def query_ollama(prompt, model_name="llama3.2", persona_content="", external_context=""):
    """
    Query the Ollama model with the given prompt and persona content.
    """
    external_context = """
    You should NEVER do roleplay actions. If you are not explicitly stated to be a virtual assistant,
    you should NEVER respond in the manner of a virtual assistant.
    """  # Test context

    try:
        full_prompt = f"""
        Rules to follow when responding:\n\n
        System: {external_context}\n
        {persona_content}\n\n
        User: {prompt}"""
        
        ollama_exe_path = os.path.join(os.path.dirname(__file__), "Ollama", "ollama.exe")
        command = [ollama_exe_path, "run", model_name]
        result = subprocess.run(
            command,
            input=full_prompt,
            text=True,
            capture_output=True,
            encoding="utf-8",
            shell=False,  # safe to keep shell=False
        )
        if result.returncode != 0:
            logging.error(f"Error querying Ollama model: {result.stderr}")
            return "Error: Unable to process your request."
        response = result.stdout.strip()
        logging.info("Received response from Ollama model.")
        return response
    except subprocess.CalledProcessError as e:
        logging.error(f"Subprocess error during Ollama query: {e}")
        return "Error: Unable to process your request."
    except Exception as e:
        logging.error(f"Unexpected error during Ollama query: {e}")
        return "Error: Unable to process your request."

# If mode is openai, import and initialize openai API. If ollama, start ollama server.
if mode == "ollama":
    start_ollama_server()
    openai_enabled = False
else:
    from openai_api import get_response
    openai_enabled = True

@app.route("/query", methods=["POST"])
def query():
    """
    Endpoint to handle user queries and return responses from the chosen backend.
    """
    data = request.get_json()
    user_query = data.get("query", "")
    persona_prompt = data.get("persona_prompt", "You are a program called ALTER EGO.") # Default persona prompt in order to warm up the server
    voice_model_name = data.get("voice_model_name", None)

    # Validate inputs
    if not user_query or not isinstance(user_query, str):
        return jsonify({"error": "Invalid query"}), 400
    if not persona_prompt or not isinstance(persona_prompt, str):
        return jsonify({"error": "Invalid persona prompt"}), 400

    # Use the chosen backend
    if mode == "ollama":
        answer = query_ollama(
            user_query, model_name="llama3.2", persona_content=persona_prompt
        )
    elif mode == "openai" and openai_enabled:
        answer = get_response(user_query, system_prompt=persona_prompt)
    else:
        return jsonify({"error": "Backend not supported"}), 400

    # Detect emotions
    query_emotions_list = detect_emotions([user_query])
    response_emotions_list = detect_emotions([answer])

    query_emotions = query_emotions_list[0] if query_emotions_list else {}
    response_emotions = response_emotions_list[0] if response_emotions_list else {}

    # Load voice models
    models_path = os.path.join(
        os.path.dirname(__file__), "../persistentdata/elevenlabs_models.json"
    )
    try:
        with open(models_path, "r", encoding="utf-8") as f:
            voice_models = json.load(f)
    except Exception as e:
        logging.error(f"Error reading elevenlabs_models.json: {e}")
        voice_models = {}

    audio_base64 = None

    # Only do TTS if voice model chosen
    if voice_model_name and voice_model_name in voice_models:
        voice_id = voice_models[voice_model_name]
        model_id = "eleven_multilingual_v2"

        response_audio = convert_text_to_speech(voice_id, model_id, answer)
        if response_audio:
            audio_base64 = base64.b64encode(response_audio).decode("utf-8")

    return jsonify(
        {
            "response": answer,
            "query_emotions": query_emotions,
            "response_emotions": response_emotions,
            "audio_base64": audio_base64,
        }
    )

if __name__ == "__main__":
    print("Starting production server on http://127.0.0.1:5000")
    serve(app, host="127.0.0.1", port=5000)