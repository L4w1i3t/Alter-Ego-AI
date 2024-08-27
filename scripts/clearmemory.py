# clearmemory.py
# Run the neuralyzer.bat file to run this file and clear all character files' memory
import os

# Directory where character memory files are stored
CHARACTER_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "characterdata")

# Function to delete all memory JSON files in the characterdata folder
def clear_memory_files():
    try:
        # Get a list of all files in the directory
        for file_name in os.listdir(CHARACTER_DATA_DIR):
            # Check if the file is a JSON memory file by ensuring it ends with "_mem.json"
            if file_name.endswith('_mem.json'):
                file_path = os.path.join(CHARACTER_DATA_DIR, file_name)
                # Remove the file
                os.remove(file_path)
                print(f"Deleted: {file_path}")
                
        print("All memory files have been deleted.")
        
    except Exception as e:
        print(f"An error occurred: {str(e)}")

clear_memory_files()