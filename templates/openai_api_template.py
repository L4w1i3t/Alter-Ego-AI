# openai_api.py
from openai import OpenAI
import openai
import dotenv
import os

# Load environment variables
dotenv.load_dotenv()

openai_api_key = os.getenv('OPENAI_API_KEY')
if not openai_api_key:
    exit("No OpenAI API Key found.")
print("OpenAI API Key loaded successfully.")
client = OpenAI(api_key = openai_api_key)

# Doc Bookkeeping:
# roles - system, user, assistant
# system - sets the behavior
# user - provides requests or comments to respond to
# assistant - stores previous responses

MODEL="gpt-4o"

def get_query(query):
    completion = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "system", 
                # THIS IS WHERE THE CHARACTER DATA IS STORED
                "content": "Your responses should not be any larger than 100 words (ASCII)."
                },
            {
                "role": "user",
                "content": query
                }
        ],
        max_tokens=100
    )
    return completion.choices[0].message.content