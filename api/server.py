# api/server.py

import sys
import os
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List
import io

# Assumes 'api' and 'model' are sibling directories
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
model_dir = os.path.join(parent_dir, "model")
sys.path.append(parent_dir)

# Importing functionalities from the model modules
from model.elevenlabs_api import generate_audio, change_voice_model
from model.textgen_gpt import get_query
from model.emotions import detect_emotions

from fastapi.middleware.cors import CORSMiddleware

# Initialize FastAPI app
app = FastAPI(
    title="ALTER EGO API SERVER",
    description="API for generating text, audio, and emotion detection based on character data.",
    version="1.0.0"
)

# -------------------------------
# CORS Configuration
# -------------------------------

origins = [
    "file://",  # Allow Electron app
    # Add other origins if needed
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development; restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------------
# Pydantic Models for Requests
# -------------------------------

class GenerateTextRequest(BaseModel):
    query: str
    character_file: str
    character_data: str

class GenerateAudioRequest(BaseModel):
    text: str

class DetectEmotionsRequest(BaseModel):
    texts: List[str]
    score_threshold: float = 0.01  # Default threshold

class ChangeVoiceModelRequest(BaseModel):
    voice_model_name: str  # Renamed to avoid conflict

# -------------------------------
# API Endpoints
# -------------------------------

@app.post("/generate-text", summary="Generate text based on a user query and character data.")
def generate_text_endpoint(request: GenerateTextRequest):
    """
    Generate a response from the AI character based on the user query and character data.
    """
    try:
        response = get_query(request.query, request.character_file, request.character_data)
        return {"response": response}
    except Exception as e:
        # Log the error as needed
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate-audio", summary="Generate audio from text using ElevenLabs.")
def generate_audio_endpoint(request: GenerateAudioRequest):
    """
    Generate audio bytes from the provided text.
    """
    try:
        audio_bytes = generate_audio(request.text)
        return StreamingResponse(io.BytesIO(audio_bytes), media_type="audio/mpeg")
    except Exception as e:
        # Log the error as needed
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/detect-emotions", summary="Detect emotions in the provided texts.")
def detect_emotions_endpoint(request: DetectEmotionsRequest):
    """
    Analyze a list of texts and detect emotions present in each.
    """
    try:
        emotions = detect_emotions(request.texts, request.score_threshold)
        return {"emotions": emotions}
    except Exception as e:
        # Log the error as needed
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/change-voice-model", summary="Change the current voice model for audio generation.")
def change_voice_model_endpoint(request: ChangeVoiceModelRequest):
    """
    Change the voice model used for generating audio.
    """
    try:
        change_voice_model(request.voice_model_name)  # Updated parameter
        return {"status": "Voice model changed successfully."}
    except ValueError as ve:
        # Voice model not found
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        # Other errors
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health", summary="Health check endpoint.")
def health_check():
    """
    Simple health check to verify that the API is running.
    """
    return {"status": "API is running"}

# -------------------------------
# Run the Server
# -------------------------------

if __name__ == "__main__":
    import uvicorn
    # Running on host 0.0.0.0 to be accessible externally. Adjust as needed.
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=False)
