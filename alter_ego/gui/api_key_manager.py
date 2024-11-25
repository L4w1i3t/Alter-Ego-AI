# api_key_manager.py

import os
import json
import logging

logging.basicConfig(level=logging.INFO)


class APIKeyManager:
    def __init__(self):
        # Define the path to keys.json relative to this file
        self.keys_file_path = os.path.join(
            os.path.dirname(__file__), "../persistent/keys.json"
        )
        self.keys = self.load_keys()

    def load_keys(self):
        """Load API keys from the JSON file."""
        try:
            with open(self.keys_file_path, "r", encoding="utf-8") as f:
                keys = json.load(f)
            logging.info("API keys loaded successfully from keys.json.")
            return keys
        except FileNotFoundError:
            logging.error(f"keys.json not found at {self.keys_file_path}.")
            return {}
        except json.JSONDecodeError as e:
            logging.error(f"Error decoding keys.json: {str(e)}")
            return {}
        except Exception as e:
            logging.error(f"Unexpected error loading keys.json: {str(e)}")
            return {}

    def get_api_key(self, service):
        """Retrieve the API key for a given service."""
        return self.keys.get(service.upper() + "_API_KEY")

    def update_api_key(self, service, new_key):
        """Update or add an API key for a service."""
        try:
            service_key = service.upper() + "_API_KEY"
            self.keys[service_key] = new_key
            with open(self.keys_file_path, "w", encoding="utf-8") as f:
                json.dump(self.keys, f, indent=4)
            logging.info(f"Successfully updated API key for {service}.")
            return True
        except Exception as e:
            logging.error(f"Error updating API key: {str(e)}")
            return False

    def remove_api_key(self, service):
        """Remove an API key for a service."""
        try:
            service_key = service.upper() + "_API_KEY"
            if service_key in self.keys:
                del self.keys[service_key]
                with open(self.keys_file_path, "w", encoding="utf-8") as f:
                    json.dump(self.keys, f, indent=4)
                logging.info(f"Successfully removed API key for {service}.")
                return True
            else:
                logging.warning(f"API key for {service} does not exist.")
                return False
        except Exception as e:
            logging.error(f"Error removing API key: {str(e)}")
            return False