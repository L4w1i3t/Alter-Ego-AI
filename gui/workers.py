# workers.py
import sounddevice as sd
import numpy as np
import whisper
import logging
from PyQt5.QtCore import QThread, pyqtSignal

# Necessary API functions
from model.textgen_gpt import get_query as get_query_gpt
from model.textgen_llama import get_query as get_query_llama
from model.elevenlabs_api import generate_audio

# Load Whisper Model (options: tiny, base, small, medium, large)
whisper_model = whisper.load_model('tiny')

# Worker Thread to handle the API call
class QueryWorker(QThread):
    result_ready = pyqtSignal(str)
    error_occurred = pyqtSignal(str)

    def __init__(self, query, character_file, character_data, text_generation_model='openai'):
        super().__init__()
        self.query = query
        self.character_file = character_file
        self.character_data = character_data
        self.text_generation_model = text_generation_model

    def run(self):
        try:
            if self.text_generation_model == 'openai':
                response = get_query_gpt(self.query, self.character_file, self.character_data, model_name='gpt')
            elif self.text_generation_model == 'ollama':
                response = get_query_llama(self.query, self.character_file, self.character_data, model_name='ollama')
            else:
                raise ValueError(f"Unknown text generation model: {self.text_generation_model}")
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
        self._is_stopped = False

    def run(self):
        try:
            self.recognition_started.emit()

            print("Speech Recognition Enabled...")
            audio_data = self.record_audio()

            if self._is_stopped:
                print("Speech recognition was stopped before transcription.")
                self.recognition_stopped.emit()
                return

            transcription = self.transcribe_audio_with_whisper(audio_data)

            self.recognized_text.emit(transcription)
            self.recognition_stopped.emit()

        except Exception as e:
            logging.error(f"Exception in SpeechRecognitionWorker: {e}", exc_info=True)
            self.error_occurred.emit(str(e))

    def record_audio(self):
        try:
            audio_data = sd.rec(
                int(self.duration * self.sample_rate),
                samplerate=self.sample_rate,
                channels=1,
                dtype='float32'
            )
            sd.wait()
            audio_data = np.squeeze(audio_data)
            audio_data = np.clip(audio_data, -1.0, 1.0)
            audio_data = np.nan_to_num(audio_data, nan=0.0, posinf=1.0, neginf=-1.0)
            return audio_data
        except Exception as e:
            print(f"Error during audio recording: {e}")
            self._is_stopped = True
            raise e

    def transcribe_audio_with_whisper(self, audio_data):
        print("Transcribing audio with Whisper...")
        if audio_data.dtype != np.float32:
            audio_data = audio_data.astype(np.float32)

        result = whisper_model.transcribe(audio_data)
        transcription = result['text']
        print(f"Recognized: {transcription}")
        return transcription

    def stop(self):
        self._is_stopped = True
        sd.stop()


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