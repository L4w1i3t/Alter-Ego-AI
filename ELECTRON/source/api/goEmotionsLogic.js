// goEmotionsLogic.js
// Implements text-to-emotion conversion using Hugging Face's transformers.js pipeline,
// specifically the ONNX version of the model for multi-label classification.

let classifier = null;

/**
 * Dynamically loads and initializes the text-classification pipeline.
 */
async function loadClassifier() {
  if (!classifier) {
    // Dynamically import the pipeline function from transformers.js provided by Hugging Face.
    const { pipeline } = await import('@huggingface/transformers');

    // Load the pipeline for text-classification using the ONNX model:
    // "SamLowe/roberta-base-go_emotions-onnx"
    // We'll specify function_to_apply: 'sigmoid' for multi-label
    // and top_k: 28 to ensure we get all labels.
    classifier = await pipeline('text-classification', 'SamLowe/roberta-base-go_emotions-onnx', {
      function_to_apply: 'sigmoid', // For multi-label output
      top_k: 28,                    // Return all 28 possible labels
      multi_label: true,            // Enable multi-label classification
      return_all_scores: true,      // Return all label scores
    });
  }
  return classifier;
}

/**
 * Detects emotions for an array of texts.
 * @param {string[]} texts - An array of input texts.
 * @returns {Promise<Array>} - A promise resolving to an array of emotion predictions per input.
 */
async function detectEmotions(texts) {
  const clf = await loadClassifier();
  const results = [];
  for (const text of texts) {
    // Each call returns an array of { label, score } objects.
    const output = await clf(text);

    // Filter out labels with scores below the threshold.
    results.push(output);
  }
  return results;
}

module.exports = { detectEmotions };
