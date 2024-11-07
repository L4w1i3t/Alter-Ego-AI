# clearmemory.py
# Run this script to clear all character memory databases for both OpenAI and Ollama models
import os

# Directory where character memory files are stored
CHARACTER_DATA_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "memory_databases"
)


# Function to delete all memory SQLite database files in the memory_databases folder
def clear_memory_files():
    try:
        # Get a list of all files in the directory
        for file_name in os.listdir(CHARACTER_DATA_DIR):
            # Check if the file is a SQLite memory file by ensuring it ends with "_memory.db"
            if file_name.endswith("_memory.db"):
                file_path = os.path.join(CHARACTER_DATA_DIR, file_name)
                # Remove the file
                os.remove(file_path)
                print(f"Deleted: {file_path}")

        print("All memory files have been deleted.")

    except Exception as e:
        print(f"An error occurred: {str(e)}")


clear_memory_files()
