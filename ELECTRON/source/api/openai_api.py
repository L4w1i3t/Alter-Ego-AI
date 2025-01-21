import openai
import logging
from keys_util import load_keys

# Configure logging to display debug messages
logging.basicConfig(level=logging.DEBUG)

# Load API keys from the keys.json file
keys = load_keys()
openai.api_key = keys.get("OPENAI_API_KEY", "")

def get_response(user_query, system_prompt=None, model="gpt-3.5-turbo", temperature=0.7):
    """
    Generate a response from OpenAI's chat.completions endpoint.
    Args:
        user_query (str): The user's input query.
        system_prompt (str, optional): An optional system prompt to guide the model's behavior.
        model (str): The model to use for generating the response.
        temperature (float): The sampling temperature to use. Higher values mean more random completions.
    Returns:
        str: The generated response from the model.
    """
    if not openai.api_key:
        # No valid API key found
        return "Error: OpenAI API Key not configured. The server will continue running, but OpenAI features are disabled."

    # Prepare the messages for the chat.completions API
    system_prompt = """
    You should NEVER do roleplay actions. If you are not explicitly stated to be a virtual assistant,
    you should NEVER respond in the manner of a virtual assistant.
    """  # Test context
    
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": user_query})

    try:
        # Call the OpenAI chat.completions API to generate a response
        response = openai.chat.completions.create(
            model=model, messages=messages, temperature=temperature
        )
        # Extract and return the content of the first choice
        return response.choices[0].message.content.strip()
    except Exception as e:
        # Log any errors that occur during the API call
        logging.error("OpenAI API Error: %s", e)
        return f"An error occurred: {e}"