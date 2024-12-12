import warnings
from transformers import pipeline, RobertaTokenizer

# Suppress the specific FutureWarning related to clean_up_tokenization_spaces
warnings.filterwarnings(
    "ignore", category=FutureWarning, module="transformers.tokenization_utils_base"
)

# Load the pre-trained emotion detection model and tokenizer once
emotion_classifier = pipeline(
    "text-classification", model="SamLowe/roberta-base-go_emotions", top_k=None
)
tokenizer = RobertaTokenizer.from_pretrained("SamLowe/roberta-base-go_emotions")

MAX_TOKEN_LENGTH = 512

def truncate_text(text, max_length=MAX_TOKEN_LENGTH):
    tokenized_text = tokenizer(
        text,
        add_special_tokens=True,
        truncation=True,
        max_length=max_length,
        return_tensors="pt",
    )
    return tokenizer.decode(tokenized_text["input_ids"][0], skip_special_tokens=True)

def detect_emotions(texts, score_threshold=0.01):
    # Truncate texts if necessary
    truncated_texts = [truncate_text(text) for text in texts]

    # Get emotion predictions for all input texts
    try:
        all_emotions = emotion_classifier(truncated_texts)
    except Exception as e:
        print(f"Error in emotion_classifier: {e}")
        return []

    results = []
    for emotions in all_emotions:
        # Filter out emotions with a score below the threshold
        filtered_emotions = {
            result["label"]: result["score"]
            for result in emotions
            if result["score"] >= score_threshold
        }

        # Sort emotions by score descending
        sorted_emotions = dict(
            sorted(filtered_emotions.items(), key=lambda item: item[1], reverse=True)
        )
        results.append(sorted_emotions)

    return results