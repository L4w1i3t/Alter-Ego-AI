# emotions_api.py
import warnings
from transformers import pipeline

# Suppress the specific FutureWarning related to clean_up_tokenization_spaces cause screw you huggingface
warnings.filterwarnings("ignore", category=FutureWarning, module="transformers.tokenization_utils_base")

# Load the pre-trained emotion detection model
emotion_classifier = pipeline(
    "text-classification", 
    model="SamLowe/roberta-base-go_emotions", 
    top_k=None
)

"""
List of emotions for this model (case insensitive):
admiration
amusement
anger
annoyance
approval
caring
confusion
curiosity
desire
disappointment
disapproval
disgust
embarrassment
excitement
fear
gratitude
grief
joy
love
neutral
nervousness
optimism
pride
realization
relief
remorse
sadness
surprise
"""

def detect_emotions(texts, score_threshold=0.01):
    # Get emotion predictions for all input texts
    all_emotions = emotion_classifier(texts)
    
    # Process each text's emotion results
    results = []
    for emotions in all_emotions:
        # Filter out emotions with a score below the threshold
        filtered_emotions = {result['label']: result['score'] for result in emotions if result['score'] >= score_threshold}
        # Sort emotions by score in descending order
        sorted_emotions = dict(sorted(filtered_emotions.items(), key=lambda item: item[1], reverse=True))
        results.append(sorted_emotions)
    
    return results

# Test cases
sample_texts = [
    "I'm so happy today! Everything is going great.",
    "I'm feeling really down and sad.",
    "I'm so angry right now! This is frustrating.",
    "I mean, it's alright, like... Overrated as fuck in my opinion.",
    "I'm so excited about this new opportunity!",
    "OH MY GOD, WHY THE FUCK WOULD YOU DO THAT?! DO YOU KNOW HOW BADLY YOU SCREWED UP?!",
    "Ewwwwwwwww, that's gross..."
]

# Get emotions for all tests. Commented out for right now
#emotions_list = detect_emotions(sample_texts)

# Display the results. Commented out for right now
#for text, emotions in zip(sample_texts, emotions_list):
    #print(f"Text: \"{text}\"")
    #print("Detected Emotions:")
    #if emotions:
        #for emotion, score in emotions.items():
            #print(f"  {emotion.capitalize():<15}: {score:.2f}")
    #else:
        #print("  No significant emotions detected.")
    #print()