from transformers import pipeline
import os

pipe = pipeline("text-classification", model="SamLowe/roberta-base-go_emotions")