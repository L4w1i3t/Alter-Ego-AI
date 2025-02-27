import openai
import logging
from keys_util import load_keys

# Configure logging to display debug messages
logging.basicConfig(level=logging.DEBUG)

# Load API keys from the keys.json file
keys = load_keys()
openai.api_key = keys.get("OPENAI_API_KEY", "")

def get_chat_completion(messages: list[dict], model: str = "chatgpt-4o-latest", temperature: float = 0.7) -> str:
    """
    Generate a response from OpenAI's chat.completions endpoint using a list of messages.
    
    Args:
        messages (list of dict): 
            A list of messages, each a dict with:
                {
                    "role": "system" or "user" or "assistant",
                    "content": "some text"
                }
        model (str): The model to use for generating the response.
        temperature (float): Sampling temperature. Higher = more creative.
    
    Returns:
        str: The generated response text, or an error message string.
    """
    if not openai.api_key:
        # No valid API key found
        return "Error: OpenAI API Key not configured. The server will continue running, but OpenAI features are disabled."

    try:
        response = openai.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            timeout=30  # Added timeout to prevent hanging
        )
        # Return the text from the first choice
        return response.choices[0].message.content.strip()
    except Exception as e:
        logging.exception("OpenAI API Error:")
        return f"An error occurred: {e}"
