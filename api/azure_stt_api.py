# azure_stt_api.py
"""THIS API USE IS NOW DEPRECATED FOR THE PROGRAM. ALTER EGO NOW USES OPENAI WHISPER."""
import os
import azure.cognitiveservices.speech as speechsdk
import dotenv

# Load environment variables
dotenv.load_dotenv()

# Retrieve Azure subscription key and region from environment variables
subscription_key = os.getenv("AZURE_API_KEY")
region = os.getenv("AZURE_REGION")

# Check if the Azure API key and region are set
if not subscription_key:
    exit("No Azure API Key found.")
if not region:
    exit("No Azure Region found.")

print("Azure API Key loaded successfully.")
print("Azure Region loaded successfully.")

# Initialize the SpeechConfig with your subscription key and region
speech_config = speechsdk.SpeechConfig(subscription=subscription_key, region=region)