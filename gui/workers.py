# workers.py
import sounddevice as sd
import numpy as np
import whisper
from PyQt5.QtCore import QThread, pyqtSignal

# Necessary API functions
from api.openai_api import get_query
from api.elevenlabs_api import generate_audio

# Load Whisper Model (options: tiny, base, small, medium, large)
whisper_model = whisper.load_model('base')


# Worker Thread to handle the API call
class QueryWorker(QThread):
    result_ready = pyqtSignal(str)
    error_occurred = pyqtSignal(str)

    def __init__(self, query, character_file, character_data):
        super().__init__()
        self.query = query
        self.character_file = character_file
        self.character_data = character_data

    def run(self):
        try:
            response = get_query(self.query, self.character_file, self.character_data)
            self.result_ready.emit(response)
        except Exception as e:
            self.error_occurred.emit(str(e))


# Worker Thread to handle Speech Recognition
class SpeechRecognitionWorker(QThread):
    recognized_text = pyqtSignal(str)
    recognition_started = pyqtSignal()
    recognition_stopped = pyqtSignal()
    error_occurred = pyqtSignal(str)

    def __init__(self, sample_rate=16000, duration=10):
        super().__init__()
        self.sample_rate = sample_rate
        self.duration = duration

    def run(self):
        try:
            self.recognition_started.emit()

            # Record audio using sounddevice
            print("Speech Recognition Enabled...")
            audio_data = self.record_audio()

            # Perform speech recognition using Whisper
            transcription = self.transcribe_audio_with_whisper(audio_data)

            # Emit the recognized text
            self.recognized_text.emit(transcription)

            self.recognition_stopped.emit()

        except Exception as e:
            self.error_occurred.emit(str(e))

    def record_audio(self):
        audio_data = sd.rec(
            int(self.duration * self.sample_rate),
            samplerate=self.sample_rate,
            channels=1,
            dtype='float32'
        )
        sd.wait()  # Wait until the recording is finished
        audio_data = np.squeeze(audio_data)

        # Ensure the audio data is within the valid range [-1.0, 1.0]
        audio_data = np.clip(audio_data, -1.0, 1.0)

        # Handle any NaN or infinite values
        audio_data = np.nan_to_num(audio_data, nan=0.0, posinf=1.0, neginf=-1.0)

        return audio_data

    def transcribe_audio_with_whisper(self, audio_data):
        print("Transcribing audio with Whisper...")
        # Whisper expects audio data as a NumPy array with dtype float32
        if audio_data.dtype != np.float32:
            audio_data = audio_data.astype(np.float32)

        # Perform transcription
        result = whisper_model.transcribe(audio_data, condition_on_previous_text=False)
        transcription = result['text']
        print(f"Recognized: {transcription}")
        return transcription

    def stop(self):
        sd.stop()
        self.recognition_stopped.emit()


# Worker Thread for generating ElevenLabs audio
class ElevenLabsAudioWorker(QThread):
    audio_ready = pyqtSignal(bytes)
    error_occurred = pyqtSignal(str)

    def __init__(self, text):
        super().__init__()
        self.text = text

    def run(self):
        try:
            audio_bytes = generate_audio(self.text)
            self.audio_ready.emit(audio_bytes)
        except Exception as e:
            self.error_occurred.emit(str(e))
