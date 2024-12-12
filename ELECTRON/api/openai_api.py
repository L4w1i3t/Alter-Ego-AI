import os
import json
import openai

# Load keys from keys.json
keys_path = os.path.join(os.path.dirname(__file__), '../persistentdata/keys.json')
with open(keys_path, 'r', encoding='utf-8') as f:
    keys = json.load(f)

openai.api_key = keys.get('OPENAI_API_KEY', '')

def get_response(user_query, system_prompt=None, model="gpt-3.5-turbo", temperature=0.7):
    """
    Generate a response from OpenAI's ChatCompletion endpoint.
    
    Parameters:
    - user_query (str): The user's question or query.
    - system_prompt (str, optional): The system-level message (persona prompt).
    - model (str, optional): The OpenAI model to use.
    - temperature (float, optional): The temperature for response randomness.

    Returns:
    - str: The assistant's response.
    """
    if not openai.api_key:
        return "Error: OpenAI API Key not configured."

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": user_query})

    try:
        response = openai.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print("OpenAI API Error:", e)
        return f"An error occurred: {e}"