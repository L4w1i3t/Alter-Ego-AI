# api_key_manager.py
import os
from dotenv import load_dotenv, set_key, find_dotenv
import logging

logging.basicConfig(level=logging.INFO)

class APIKeyManager:
    def __init__(self):
        self.dotenv_path = find_dotenv()
        if not self.dotenv_path:
            self.dotenv_path = '.env'
        load_dotenv(self.dotenv_path)

    def get_api_key(self, service):
        """Get the current API key for a service."""
        key_mapping = {
            'openai': 'OPENAI_API_KEY',
            'elevenlabs': 'ELEVENLABS_API_KEY'
        }
        if service not in key_mapping:
            raise ValueError(f"Unknown service: {service}")
        return os.getenv(key_mapping[service])

    def update_api_key(self, service, new_key):
        """Update or add an API key for a service."""
        try:
            key_mapping = {
                'openai': 'OPENAI_API_KEY',
                'elevenlabs': 'ELEVENLABS_API_KEY'
            }
            if service not in key_mapping:
                raise ValueError(f"Unknown service: {service}")
            
            env_key = key_mapping[service]
            set_key(self.dotenv_path, env_key, new_key, quote_mode='never')  # Prevent quotes
            os.environ[env_key] = new_key
            logging.info(f"Successfully updated API key for {service}")
            return True
        except Exception as e:
            logging.error(f"Error updating API key: {str(e)}")
            return False

    def remove_api_key(self, service):
        """Remove an API key for a service."""
        try:
            key_mapping = {
                'openai': 'OPENAI_API_KEY',
                'elevenlabs': 'ELEVENLABS_API_KEY'
            }
            if service not in key_mapping:
                raise ValueError(f"Unknown service: {service}")
            
            env_key = key_mapping[service]
            set_key(self.dotenv_path, env_key, '', quote_mode='never')  # Prevent quotes
            os.environ[env_key] = ''
            logging.info(f"Successfully removed API key for {service}")
            return True
        except Exception as e:
            logging.error(f"Error removing API key: {str(e)}")
            return False