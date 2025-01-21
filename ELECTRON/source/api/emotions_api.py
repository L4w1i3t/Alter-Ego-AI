import warnings
import torch
from transformers import pipeline, RobertaTokenizer

# Suppress specific FutureWarning related to clean_up_tokenization_spaces from transformers library
warnings.filterwarnings(
    "ignore", category=FutureWarning, module="transformers.tokenization_utils_base"
)

# Determine if a GPU is available; if so, use it (device=0), otherwise use CPU (device=-1)
device = 0 if torch.cuda.is_available() else -1

# Load the pre-trained emotion detection model and tokenizer once
# The model used here is "SamLowe/roberta-base-go_emotions"
emotion_classifier = pipeline(
    "text-classification",
    model="SamLowe/roberta-base-go_emotions",
    top_k=None,  # Return all labels with their scores
    device=device,  # Use GPU if available, otherwise CPU
)
tokenizer = RobertaTokenizer.from_pretrained("SamLowe/roberta-base-go_emotions")

# Define the maximum token length for the model
MAX_TOKEN_LENGTH = 512

def truncate_text(text, max_length=MAX_TOKEN_LENGTH):
    """
    Truncate the input text to fit within the maximum token length.
    This ensures that the text does not exceed the model's input size limit.
    """
    tokenized_text = tokenizer(
        text,
        add_special_tokens=True,  # Add special tokens like [CLS] and [SEP]
        truncation=True,  # Truncate the text if it exceeds max_length
        max_length=max_length,  # Maximum length of the tokenized text
        return_tensors="pt",  # Return PyTorch tensors
    )
    return tokenizer.decode(tokenized_text["input_ids"][0], skip_special_tokens=True)

def detect_emotions(texts, score_threshold=0.0):
    """
    Detect emotions in a list of texts.
    Args:
        texts (list of str): List of input texts to analyze.
        score_threshold (float): Minimum score threshold for emotions to be included in the results.
    Returns:
        list of dict: List of dictionaries containing emotions and their scores for each input text.
    """
    # Truncate each text in the input list
    truncated_texts = [truncate_text(text) for text in texts]
    
    # Get raw emotion predictions from the model
    all_emotions_raw = emotion_classifier(truncated_texts)

    results = []
    for emotions in all_emotions_raw:
        # Convert list of emotions to a dictionary {label: score}
        emotion_dict = {e["label"]: e["score"] for e in emotions}

        # Normalize the scores so that they sum to 1
        total = sum(emotion_dict.values())
        if total > 0:
            for label in emotion_dict:
                emotion_dict[label] = emotion_dict[label] / total

        # Sort emotions by score in descending order
        emotion_dict = dict(
            sorted(emotion_dict.items(), key=lambda item: item[1], reverse=True)
        )

        # Round scores to 3 decimal places for readability
        emotion_dict = {label: round(score, 3) for label, score in emotion_dict.items()}
        results.append(emotion_dict)

    return results