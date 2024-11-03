# api/api_server.py
import sys
import os
# Assumes 'api' and 'model' are sibling directories
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
model_dir = os.path.join(parent_dir, "model")
sys.path.append(parent_dir)