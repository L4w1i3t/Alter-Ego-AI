import base64
import json
import os
import logging
import platform
import sys
from flask import Flask, request, jsonify
from waitress import serve
from datetime import datetime, timezone
import time

# Add the current directory to sys.path once for local imports.
sys.path.append(os.path.dirname(__file__))

# Local imports
from emotions_api import detect_emotions
from elevenlabs_api import convert_text_to_speech
from db_memory import SQLMemory
from ollama_manager import start_server, stop_server, query_ollama
from openai_manager import query_openai, warmup_openai

# Flask App Setup
app = Flask(__name__)
logging.basicConfig(level=logging.DEBUG)

# Determine backend mode
mode = os.environ.get("MODEL_BACKEND", "ollama")
openai_enabled = True if mode == "openai" else False

# Track warm-up status to avoid repeating expensive operations
warm_up_completed = False
memory_managers = {}

# Global cache for voice models
VOICE_MODELS = None

def get_voice_models():
    global VOICE_MODELS
    if VOICE_MODELS is None:
        models_path = os.path.join(os.path.dirname(__file__), "../persistentdata/elevenlabs_models.json")
        try:
            with open(models_path, "r", encoding="utf-8") as f:
                VOICE_MODELS = json.load(f)
        except Exception as e:
            logging.error(f"Error reading elevenlabs_models.json: {e}")
            VOICE_MODELS = {}
    return VOICE_MODELS

def get_memory_manager(persona_name):
    """Get or create the memory manager for a persona"""
    if persona_name not in memory_managers:
        memory_managers[persona_name] = SQLMemory(persona_name=persona_name)
    return memory_managers[persona_name]

@app.route("/clear_stm", methods=["POST"])
def clear_stm():
    """Clear all memory managers"""
    global memory_managers
    try:
        for persona_name, memory_manager in memory_managers.items():
            try:
                memory_manager.clear()
                logging.info(f"Successfully cleared memory for {persona_name}")
            except Exception as e:
                logging.error(f"Failed to clear memory for {persona_name}: {e}")
        
        memory_managers = {}
        logging.info("All memories have been cleared.")
        return "OK", 200
        
    except Exception as e:
        logging.exception(f"Error in clear_stm: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/stop", methods=["POST"])
def stop():
    stop_server()
    shutdown_server = request.environ.get("werkzeug.server.shutdown")
    if shutdown_server is not None:
        shutdown_server()
    return '', 204

@app.route("/status", methods=["GET"])
def status():
    """Simple endpoint to check if server is responding"""
    return jsonify({"status": "ok", "mode": mode, "warmed_up": warm_up_completed}), 200

@app.route("/query", methods=["POST"])
def query():
    global warm_up_completed
    
    data = request.get_json()
    user_query = data.get("query", "")
    persona_name = data.get("persona_name", "ALTER EGO")
    persona_prompt = data.get("persona_prompt", "You are a program called ALTER EGO.")
    voice_model_name = data.get("voice_model_name", None)

    # Get memory manager for this persona
    memory = get_memory_manager(persona_name)
    stm_buffer = memory.get_stm()

    if not user_query or not isinstance(user_query, str):
        return jsonify({"error": "Invalid query"}), 400
    if not persona_prompt or not isinstance(persona_prompt, str):
        return jsonify({"error": "Invalid persona prompt"}), 400

    # Warm-up logic with timeouts and better error handling
    if user_query.strip().lower() == "warm-up":
        if warm_up_completed:
            logging.info("Warm-up already completed, skipping")
            return jsonify({
                "response": "(Warming up complete)",
                "query_emotions": {},
                "response_emotions": {},
                "audio_base64": None
            })
        
        logging.info("Beginning warm-up process...")
        start_time = time.time()
        max_warm_up_time = 30  # 30 seconds timeout for warm-up
        
        try:
            if mode == "ollama":
                # Simplified Ollama warm-up with timeout
                final_prompt = "User: hello\nAssistant:"
                answer = query_ollama(final_prompt, persona_content=persona_prompt, timeout=max_warm_up_time)
            else:
                answer = warmup_openai()
                
            warm_up_completed = True
            logging.info(f"Warm-up completed successfully in {time.time() - start_time:.2f}s")
            
            return jsonify({
                "response": "(Warming up complete)",
                "query_emotions": {},
                "response_emotions": {},
                "audio_base64": None
            })
            
        except Exception as e:
            logging.error(f"Warm-up failed: {str(e)}")
            if time.time() - start_time >= max_warm_up_time:
                logging.warning("Warm-up timed out, continuing anyway")
            
            return jsonify({
                "response": "(Warming up encountered issues, but you can continue)",
                "query_emotions": {},
                "response_emotions": {},
                "audio_base64": None,
                "warning": "Warm-up incomplete, performance will be affected"
            })

    # Regular query handling - proceed even if warm-up failed
    try:
        # Retrieve long-term memory
        ltm_results = memory.search_similar(user_query, top_k=3)
        relevant_context = ""
        
        if ltm_results:
            relevant_memories = []
            for (chunk_text, similarity, _) in ltm_results:
                if similarity > 0.4:
                    relevant_memories.append(f"• {chunk_text.strip()} (relevance: {similarity:.2f})")
            if relevant_memories:
                relevant_context = "Relevant previous conversations:\n" + "\n".join(relevant_memories)
            else:
                relevant_context = ""

        if mode == "ollama":
            recent_exchanges = stm_buffer[-6:] if len(stm_buffer) >= 6 else stm_buffer
            memory_text = ""
            for entry in recent_exchanges:
                if entry["role"] == "user":
                    memory_text += f"User: {entry['content']}\n"
                else:
                    memory_text += f"Assistant: {entry['content']}\n"
            
            if relevant_context:
                final_prompt = (
                    f"{relevant_context}\n\n"
                    f"{memory_text}"
                    f"User: {user_query}\nAssistant:"
                )
            else:
                final_prompt = (
                    f"{memory_text}"
                    f"User: {user_query}\nAssistant:"
                )
                
            answer = query_ollama(final_prompt, persona_content=persona_prompt)
            if answer.startswith("Error:"):
                return jsonify({"error": answer}), 400
            
            memory.add_memory(user_query, role="user")
            memory.add_memory(answer, role="assistant")
        
        elif mode == "openai" and openai_enabled:
            answer = query_openai(user_query, persona_prompt, stm_buffer, relevant_context)
            memory.add_memory(user_query, role="user")
            memory.add_memory(answer, role="assistant")
        else:
            return jsonify({"error": "Backend not supported"}), 400

        if not warm_up_completed:
            warm_up_completed = True
            logging.info("First successful query - considering system warmed up")

        query_emotions_list = detect_emotions([user_query])
        response_emotions_list = detect_emotions([answer])
        query_emotions = query_emotions_list[0] if query_emotions_list else {}
        response_emotions = response_emotions_list[0] if response_emotions_list else {}

        # TTS using cached voice models
        voice_models = get_voice_models()
        audio_base64 = None
        if voice_model_name and voice_model_name in voice_models:
            voice_id = voice_models[voice_model_name]
            model_id = "eleven_multilingual_v2"
            response_audio = convert_text_to_speech(voice_id, model_id, answer)
            if response_audio:
                audio_base64 = base64.b64encode(response_audio).decode("utf-8")

        return jsonify({
            "response": answer,
            "query_emotions": query_emotions,
            "response_emotions": response_emotions,
            "audio_base64": audio_base64,
        })
    
    except Exception as e:
        logging.exception("Error processing query")
        return jsonify({
            "error": f"Error processing query: {str(e)}",
            "response": "I'm having trouble processing your request right now."
        }), 500

@app.route("/chat_history", methods=["GET"])
def get_chat_history():
    """Get chat history for a persona"""
    persona_name = request.args.get("persona_name", "ALTER EGO")
    memory = get_memory_manager(persona_name)
    history = memory.get_chat_history()
    return jsonify({"history": history})

if __name__ == "__main__":
    if mode == "ollama":
        start_server()
    print("Starting production server on http://127.0.0.1:5000")
    serve(app, host="127.0.0.1", port=5000)
