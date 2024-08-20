# azure_stt_api.py
import os
import azure.cognitiveservices.speech as speechsdk
import dotenv
from pynput import keyboard

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

print("Your Azure API key: " + subscription_key)
print("Your Azure region: " + region)

# Initialize the SpeechConfig with your subscription key and region
speech_config = speechsdk.SpeechConfig(subscription=subscription_key, region=region)

