# api/api_server.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
from fastapi.middleware.cors import CORSMiddleware
import openai_api
import elevenlabs_api
import emotions_api
import json
import os

app = FastAPI()

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for request bodies
class QueryRequest(BaseModel):
    query: str
    character_file: str

class AudioRequest(BaseModel):
    text: str

class VoiceModelRequest(BaseModel):
    voice_model_name: str

class ChangeVoiceModelResponse(BaseModel):
    success: bool
    message: str

@app.post("/query")
async def handle_query(request: QueryRequest):
    try:
        character_data = openai_api.get_character_data(request.character_file)
        response = openai_api.get_query(request.query, request.character_file, character_data)
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate-audio")
async def generate_audio(request: AudioRequest):
    try:
        audio_bytes = elevenlabs_api.generate_audio(request.text)
        # Encode audio to base64
        import base64
        audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')
        return {"audio": audio_base64}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/detect-emotions")
async def detect_emotions_endpoint(texts: List[str]):
    try:
        emotions = emotions_api.detect_emotions(texts)
        return {"emotions": emotions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/change-voice-model")
async def change_voice_model_endpoint(request: VoiceModelRequest):
    try:
        if request.voice_model_name.lower() == 'none':
            return ChangeVoiceModelResponse(success=True, message="Voice model set to None.")
        elevenlabs_api.change_voice_model(request.voice_model_name)
        return ChangeVoiceModelResponse(success=True, message=f"Voice model changed to {request.voice_model_name}.")
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/characters")
async def list_characters():
    try:
        characters = openai_api.list_characters()
        return {"characters": characters}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/character/{character_file}")
async def get_character(character_file: str):
    try:
        character_data = openai_api.get_character_data(character_file)
        return {"character_data": character_data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/voice-models")
async def get_voice_models():
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        models_path = os.path.join(base_dir, 'elevenlabs_models.json')
        if not os.path.exists(models_path):
            raise FileNotFoundError("Voice models file not found.")
        with open(models_path, 'r') as f:
            voice_models = json.load(f)
        return {"voice_models": voice_models}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))