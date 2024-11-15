# character_manager.py

import os
import json
import shutil
from pathlib import Path


class CharacterManager:
    def __init__(self):
        # Define the path to the characterdata directory
        self.base_dir = Path(__file__).resolve().parent.parent / "characterdata"
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def list_characters(self):
        """List all .chr files in the characterdata directory."""
        return [f.stem for f in self.base_dir.glob("*.chr")]

    def get_character_path(self, character_name):
        """Get the full path of a character file."""
        return self.base_dir / f"{character_name}.chr"

    def character_exists(self, character_name):
        """Check if a character file exists."""
        return self.get_character_path(character_name).exists()

    def add_character(self, character_name, content):
        """Add a new character."""
        if self.character_exists(character_name):
            raise FileExistsError(f"Character '{character_name}' already exists.")
        with open(
            self.get_character_path(character_name), "w", encoding="utf-8"
        ) as file:
            file.write(content)

    def edit_character(self, character_name, new_content):
        """Edit an existing character."""
        if not self.character_exists(character_name):
            raise FileNotFoundError(f"Character '{character_name}' does not exist.")
        with open(
            self.get_character_path(character_name), "w", encoding="utf-8"
        ) as file:
            file.write(new_content)

    def delete_character(self, character_name):
        """Delete a character."""
        if not self.character_exists(character_name):
            raise FileNotFoundError(f"Character '{character_name}' does not exist.")
        os.remove(self.get_character_path(character_name))

    def duplicate_character(self, original_name, new_name):
        """Duplicate an existing character with a new name."""
        if not self.character_exists(original_name):
            raise FileNotFoundError(f"Character '{original_name}' does not exist.")
        if self.character_exists(new_name):
            raise FileExistsError(f"Character '{new_name}' already exists.")
        shutil.copy(
            self.get_character_path(original_name), self.get_character_path(new_name)
        )
