# workers.py
from PyQt5.QtCore import QThread, pyqtSignal

# Necessary API stuff
from api.openai_api import get_query
from api.azure_stt_api import speech_config, speechsdk
from api.elevenlabs_api import generate_audio

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

    def __init__(self):
        super().__init__()
        self.speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config)
        self._is_running = True

    def run(self):
        try:
            self.speech_recognizer.recognized.connect(self.on_recognized)
            self.speech_recognizer.session_stopped.connect(self.on_session_stopped)
            self.speech_recognizer.start_continuous_recognition()
            self.recognition_started.emit()

            while self._is_running:
                pass

        except Exception as e:
            self.error_occurred.emit(str(e))

    def stop(self):
        self._is_running = False
        self.speech_recognizer.stop_continuous_recognition()
        self.recognition_stopped.emit()

    def on_recognized(self, evt):
        if evt.result.reason == speechsdk.ResultReason.RecognizedSpeech:
            self.recognized_text.emit(evt.result.text)

    def on_session_stopped(self, evt):
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