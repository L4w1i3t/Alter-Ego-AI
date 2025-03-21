import openai
import logging
from keys_util import load_keys

# Configure logging to display debug messages
logging.basicConfig(level=logging.DEBUG)

# Load API keys from the keys.json file
keys = load_keys()
openai.api_key = keys.get("OPENAI_API_KEY", "")

def get_chat_completion(messages: list[dict], model: str = "gpt-4o-mini", temperature: float = 0.7, return_usage: bool = False):
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
        return_usage (bool): Whether to return token usage statistics.
    
    Returns:
        str or tuple: If return_usage is False, returns just the generated response text.
                      If return_usage is True, returns a tuple of (response_text, usage_dict).
    """
    if not openai.api_key:
        # No valid API key found
        error_msg = "Error: OpenAI API Key not configured. The server will continue running, but OpenAI features are disabled."
        return (error_msg, None) if return_usage else error_msg

    try:
        response = openai.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            timeout=30  # Added timeout to prevent hanging
        )
        
        # Extract the completion text
        completion_text = response.choices[0].message.content.strip()
        
        # Extract token usage if available
        usage = None
        if hasattr(response, 'usage'):
            usage = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            }
        
        return (completion_text, usage) if return_usage else completion_text
        
    except Exception as e:
        logging.exception("OpenAI API Error:")
        error_msg = f"An error occurred: {e}"
        return (error_msg, None) if return_usage else error_msg