// electron/renderer/renderer.js
const axios = require('axios');

document.addEventListener('DOMContentLoaded', () => {
  const sendButton = document.getElementById('sendButton');
  const queryInput = document.getElementById('queryInput');
  const responseDisplay = document.getElementById('responseDisplay');
  const emotionsDisplay = document.getElementById('emotionsDisplay');
  const characterCombo = document.getElementById('characterCombo');
  const voiceModelCombo = document.getElementById('voiceModelCombo');
  const changeVoiceButton = document.getElementById('changeVoiceButton');
  const avatarImage = document.getElementById('avatarImage');

  // Load available characters on startup
  async function loadCharacters() {
    try {
      const response = await axios.get('http://127.0.0.1:8000/characters');
      const characters = response.data.characters;
      characters.forEach((char) => {
        const option = document.createElement('option');
        option.value = char;
        option.text = char;
        characterCombo.add(option);
      });
    } catch (error) {
      console.error('Failed to load characters:', error);
      alert('Failed to load characters from the backend.');
    }
  }

  // Load voice models on startup
  async function loadVoiceModels() {
    try {
      const response = await axios.get('http://127.0.0.1:8000/voice-models');
      const voiceModels = response.data.voice_models;
      Object.keys(voiceModels).forEach((modelName) => {
        const option = document.createElement('option');
        option.value = modelName;
        option.text = modelName;
        voiceModelCombo.add(option);
      });
    } catch (error) {
      console.error('Failed to load voice models:', error);
      alert('Failed to load voice models from the backend.');
    }
  }

  loadCharacters();
  loadVoiceModels();

  sendButton.addEventListener('click', async () => {
    const query = queryInput.value.trim();
    const characterFile = characterCombo.value;

    if (!query || !characterFile) {
      alert('Please enter a query and select a character.');
      return;
    }

    responseDisplay.innerText = 'Thinking...';

    try {
      // Send query to FastAPI
      const queryResponse = await axios.post('http://127.0.0.1:8000/query', {
        query,
        character_file: characterFile,
      });

      const aiResponse = queryResponse.data.response;
      responseDisplay.innerText = aiResponse;

      // Detect emotions
      const emotionsResponse = await axios.post('http://127.0.0.1:8000/detect-emotions', [aiResponse]);
      const emotions = emotionsResponse.data.emotions[0];

      // Display emotions
      let emotionsText = '';
      for (const [emotion, score] of Object.entries(emotions)) {
        emotionsText += `${emotion}: ${score.toFixed(2)}\n`;
      }
      emotionsDisplay.innerText = emotionsText;

      // Update avatar based on highest emotion
      const highestEmotion = Object.keys(emotions).reduce((a, b) => emotions[a] > emotions[b] ? a : b);
      const avatarPath = `/avatars/${characterFile}/${highestEmotion}.png`;

      // Verify if the avatar image exists
      const img = new Image();
      img.onload = () => {
        avatarImage.src = avatarPath;
      };
      img.onerror = () => {
        console.warn(`Avatar image not found for emotion: ${highestEmotion}`);
        avatarImage.src = `./assets/avatars/${characterFile}/neutral.png`; // Fallback to neutral
      };
      img.src = avatarPath;

      // Generate Audio
      const audioResponse = await axios.post('http://127.0.0.1:8000/generate-audio', {
        text: aiResponse,
      });

      const audioBase64 = audioResponse.data.audio;
      const audioBytes = Uint8Array.from(atob(audioBase64), c => c.charCodeAt(0));
      const blob = new Blob([audioBytes], { type: 'audio/mpeg' });
      const url = URL.createObjectURL(blob);
      const audio = new Audio(url);
      audio.play();

    } catch (error) {
      console.error(error);
      const errorMessage = error.response ? error.response.data.detail : error.message;
      responseDisplay.innerText = `Error: ${errorMessage}`;
      alert(`Error: ${errorMessage}`);
    }
  });

  changeVoiceButton.addEventListener('click', async () => {
    const selectedModel = voiceModelCombo.value;
    const response = await axios.post('http://127.0.0.1:8000/change-voice-model', {
    voice_model_name: selectedModel,
    });
    if (!selectedModel) {
      alert('Please select a voice model.');
      return;
    }

    try {
      const response = await axios.post('http://127.0.0.1:8000/change-voice-model', {
        voice_model_name: selectedModel,
      });

      alert(response.data.message);
    } catch (error) {
      console.error(error);
      const errorMessage = error.response ? error.response.data.detail : error.message;
      alert(`Error: ${errorMessage}`);
    }
  });
});
