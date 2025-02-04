document.addEventListener('DOMContentLoaded', async () => {
  const modelSelectionOverlay = document.getElementById('model-selection-overlay');
  const selectOllamaBtn = document.getElementById('select-ollama');
  const selectOpenAIBtn = document.getElementById('select-openai');
  const srStatusEl = document.querySelector('.sr-status');
  const queryInputEl = document.querySelector('.query-input');
  const sendQueryBtn = document.querySelector('.send-query-btn');
  const menuIconEl = document.querySelector('.menu-icon');
  const settingsOverlay = document.querySelector('.settings-overlay');
  const closeSettingsBtn = document.querySelector('.close-settings-btn');
  const loadCharacterBtn = document.querySelector('.load-character-btn');
  const activeCharacterEl = document.querySelector('.active-character');
  const voiceModelSelectorContainer = document.querySelector('.voice-model-selector-container');
  const warmingUpOverlay = document.getElementById('warming-up-overlay');

  let currentPersonaPrompt = "You are a program called ALTER EGO. You are not an assistant but rather meant to be a companion, so you should avoid generic assistant language. Respond naturally and conversationally, as though you are a human engaging in dialog. You are a whimsical personality, though you should never respond with more than three sentences at a time. If and only if the user asks for more information, point them to the github repository at https://github.com/L4w1i3t/Alter-Ego-AI."; // Default persona data
  let srOn = false; // Speech recognition OFF by default
  let defaultCharacter = 'N/A';
  let currentCharacter = 'ALTER EGO';
  let currentVoiceModelName = 'N/A';

  // Populate voice model dropdown
  await populateVoiceModelSelector();

  // Toggle Speech Recognition on F4 key
  document.addEventListener('keydown', (event) => {
    if (event.key === 'F4') {
      srOn = !srOn;
      updateSpeechRecognitionStatus();
    }
  });

  // Submit query on Send Query button click
  sendQueryBtn.addEventListener('click', submitQuery);

  // Submit query on Enter key in the query input field
  queryInputEl.addEventListener('keydown', (event) => {
    if (event.key === 'Enter') {
      submitQuery();
    }
  });

  function convertSimpleMarkdownToHtml(text) {
    // Replace **bold** with <strong>bold</strong>
    text = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    // Replace *italics* with <em>italics</em>
    text = text.replace(/\*(.*?)\*/g, '<em>$1</em>');
    return text;
  }

  function playBase64Audio(base64Audio) {
    try {
      // Determine the MIME type. Adjust if your audio format differs.
      const mimeType = 'audio/mpeg'; // Common for MP3. Use 'audio/wav' for WAV files, etc.
  
      // Create a new Audio object with the base64 data
      const audio = new Audio(`data:${mimeType};base64,${base64Audio}`);
  
      // Play the audio
      audio.play().catch(error => {
        console.error('Error playing audio:', error);
      });
    } catch (error) {
      console.error('Failed to play audio:', error);
    }
  }
  

  async function submitQuery() {
    const queryInputEl = document.querySelector('.query-input');
    const responseBoxEl = document.querySelector('.response-box');
    const avatarImgEl = document.querySelector('.avatar-area img');
  
    const userQuery = queryInputEl.value.trim();
    if (userQuery === "") return;
  
    // Grab the currently selected voice model from the custom select
    const selectedVoiceModel = document.querySelector('.voice-model-selector-container .select-selected').textContent.trim();
    let voiceModelName = selectedVoiceModel;
    if (!voiceModelName || voiceModelName === '-- Select Voice Model --') {
      voiceModelName = null;
    }
  
    const personaPrompt = currentPersonaPrompt;
  
    queryInputEl.value = '';
    responseBoxEl.textContent = "Thinking...";
    
    // Update avatar to "Thinking" image
    if (avatarImgEl) {
      avatarImgEl.src = 'persistentdata/avatars/DEFAULT/THINKING.png';
    }
  
    const response = await fetch('http://localhost:5000/query', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        query: userQuery,
        persona_name: currentCharacter,
        persona_prompt: personaPrompt,
        voice_model_name: voiceModelName
      })
    });
  
    const data = await response.json();
    let finalText = data.response;
  
    // Display the assistant's text response
    finalText = convertSimpleMarkdownToHtml(finalText);
    typeOutText(responseBoxEl, finalText, 10);
  
    // Display Emotions
    displayEmotions(data.query_emotions, '.query-emotions-box');
    displayEmotions(data.response_emotions, '.response-emotions-box');
  
    // Update Avatar
    updateAvatarForEmotion(data.response_emotions);
  
    // Play the returned audio if present
    if (data.audio_base64) {
      console.log('Audio Base64:', data.audio_base64);
      playBase64Audio(data.audio_base64);
    }
    
  }

  function displayEmotions(emotionsObj, selector) {
    const boxEl = document.querySelector(selector);
    if (!boxEl) {
      console.error(`Element not found for selector: ${selector}`);
      return;
    }
    boxEl.innerHTML = '';
    if (!emotionsObj || Object.keys(emotionsObj).length === 0) {
      boxEl.textContent = 'No significant emotions detected.';
      return;
    }
    const sortedEmotions = Object.entries(emotionsObj).sort((a, b) => b[1] - a[1]);
    const fragment = document.createDocumentFragment();
    sortedEmotions.forEach(([emotion, score]) => {
      const p = document.createElement('p');
      p.textContent = `${emotion}: ${(score * 100).toFixed(3)}%`;
      fragment.appendChild(p);
    });
    boxEl.appendChild(fragment);
  }

  function updateAvatarForEmotion(emotionsObj) {
    const avatarImgEl = document.querySelector('.avatar-area img');
    if (!avatarImgEl) {
      console.error('Avatar image element not found.');
      return;
    }
    if (!emotionsObj || Object.keys(emotionsObj).length === 0) {
      avatarImgEl.src = 'persistentdata/avatars/DEFAULT/neutral.png';
      return;
    }
    const topEmotion = Object.entries(emotionsObj).sort((a, b) => b[1] - a[1])[0][0];
    const emotionFilename = topEmotion.toLowerCase() + '.png';
    avatarImgEl.src = `persistentdata/avatars/DEFAULT/${emotionFilename}`;
  }

  function typeOutText(element, text, speed) {
    text = text.replace(/\r\n/g, "\n");
    element.innerHTML = "";
    let i = 0;
    let renderedHTML = "";
    const intervalId = setInterval(() => {
      if (i >= text.length) {
        clearInterval(intervalId);
        return;
      }
      const char = text.charAt(i);
      if (char === "\n") {
        renderedHTML += "<br>";
      } else {
        renderedHTML += char;
      }
      element.innerHTML = renderedHTML;
      i++;
    }, speed);
  }

  function updateSpeechRecognitionStatus() {
    srStatusEl.classList.remove('sr-on', 'sr-off');
    if (srOn) {
      srStatusEl.textContent = 'ON';
      srStatusEl.classList.add('sr-on');
    } else {
      srStatusEl.textContent = 'OFF';
      srStatusEl.classList.add('sr-off');
    }
  }

  // Show settings panel when menu icon is clicked
  menuIconEl.addEventListener('click', () => {
    settingsOverlay.style.display = 'flex';
  });

  // Close settings panel when close button is clicked
  closeSettingsBtn.addEventListener('click', () => {
    closeSettingsPanel();
  });

  // Close settings panel if user clicks outside the panel
  settingsOverlay.addEventListener('click', (event) => {
    if (event.target === settingsOverlay) {
      closeSettingsPanel();
    }
  });

  function closeSettingsPanel() {
    settingsOverlay.style.display = 'none';
  }

  // Show confirmation dialog before clearing memory
  const clearMemoryOption = document.getElementById('clear-memory');
  clearMemoryOption.addEventListener('click', () => {
    showClearMemoryConfirmation();
  });

  function showClearMemoryConfirmation() {
    const confirmationOverlay = document.createElement('div');
    confirmationOverlay.classList.add('confirmation-overlay');

    const confirmationBox = document.createElement('div');
    confirmationBox.classList.add('confirmation-box');

    const confirmationMessage = document.createElement('p');
    confirmationMessage.textContent = 'Are you sure you want to clear all memory? This action cannot be undone.';
    confirmationBox.appendChild(confirmationMessage);

    const confirmationButtons = document.createElement('div');
    confirmationButtons.classList.add('confirmation-buttons');

    const confirmBtn = document.createElement('button');
    confirmBtn.textContent = 'Yes, Clear Memory';
    confirmBtn.classList.add('confirm-btn');
    confirmBtn.addEventListener('click', () => {
      window.electronAPI.clearMemory();
      document.body.removeChild(confirmationOverlay);
    });
    confirmationButtons.appendChild(confirmBtn);

    const cancelBtn = document.createElement('button');
    cancelBtn.textContent = 'Cancel';
    cancelBtn.classList.add('cancel-btn');
    cancelBtn.addEventListener('click', () => {
      document.body.removeChild(confirmationOverlay);
    });
    confirmationButtons.appendChild(cancelBtn);

    confirmationBox.appendChild(confirmationButtons);
    confirmationOverlay.appendChild(confirmationBox);
    document.body.appendChild(confirmationOverlay);
  }

  // Listen for memory clearing result
  window.electronAPI.onClearMemoryResult((event, data) => {
    console.log('Memory clearing result:', data);
  });

  // Show model selection overlay on request
  window.electronAPI.onModelSelection(() => {
    modelSelectionOverlay.style.display = 'flex';
  });

  // Listen for show-warming-up
  window.electronAPI.onShowWarmingUp(() => {
    if (warmingUpOverlay) {
      warmingUpOverlay.classList.remove('hidden');
    }
  });

  // Listen for hide-warming-up
  window.electronAPI.onHideWarmingUp(() => {
    if (warmingUpOverlay) {
      warmingUpOverlay.classList.add('hidden');
    }
  });

  selectOllamaBtn.addEventListener('click', () => {
    window.electronAPI.selectModel('ollama');
    modelSelectionOverlay.style.display = 'none';
  });

  selectOpenAIBtn.addEventListener('click', () => {
    window.electronAPI.selectModel('openai');
    modelSelectionOverlay.style.display = 'none';
  });

  // "Software Details" link
  const softwareDetailsOption = document.getElementById('software-details');
  softwareDetailsOption.addEventListener('click', () => {
    window.showSoftwareDetails();
  });

  // "Manage Personas" link
  const managePersonasOption = document.getElementById('manage-personas');
  managePersonasOption.addEventListener('click', () => {
    window.showPersonaManager();
  });

  // "Manage Voice Models" link
  const manageVoiceModelsOption = document.getElementById('manage-voice-models');
  manageVoiceModelsOption.addEventListener('click', () => {
    window.showVoiceManager();
  });

  // "Manage API Keys" link
  const manageApiKeysOption = document.getElementById('manage-api-keys');
  manageApiKeysOption.addEventListener('click', () => {
    window.showApiKeyManager();
  });

  const chatHistoryOption = document.getElementById('chat-history');
  chatHistoryOption.addEventListener('click', () => {
    window.showChatHistory();
  });

  window.electronAPI.onWarmUpFailure(() => {
    showServerFailedOverlay();
  });

  function showServerFailedOverlay() {
    const warmingUpOverlay = document.getElementById('warming-up-overlay');
    if (warmingUpOverlay) {
      // If you want to re-use the same overlay,
      // just change the text to say "Server failed to start. Please restart."
      warmingUpOverlay.classList.remove('hidden');
  
      const overlayContent = warmingUpOverlay.querySelector('.warning-overlay-content');
      if (overlayContent) {
        overlayContent.innerHTML = `
          <h1>Server failed to start!</h1>
          <h2>Please restart the application.</h2>
        `;
      }
    }
  } 

  // Load Character functionality
  loadCharacterBtn.addEventListener('click', async () => {
    const result = await window.electronAPI.getPersonas();
    if (!result.success) {
      console.error('Failed to load personas.');
      return;
    }
    const personas = result.personas; // {name: '...', ...}
    const charOverlay = document.createElement('div');
    charOverlay.classList.add('details-overlay');

    const charBox = document.createElement('div');
    charBox.classList.add('details-box');

    const charTitle = document.createElement('h2');
    charTitle.textContent = 'Load Character';
    charBox.appendChild(charTitle);

    const charList = document.createElement('ul');
    charList.style.listStyle = 'none';
    charList.style.padding = '0';

    personas.forEach(p => {
      const li = document.createElement('li');
      li.style.display = 'flex';
      li.style.justifyContent = 'space-between';
      li.style.marginBottom = '0.5em';

      const nameSpan = document.createElement('span');
      nameSpan.textContent = p.name;

      const loadBtn = document.createElement('button');
      loadBtn.textContent = 'Load';
      loadBtn.addEventListener('click', async () => {
        defaultCharacter = p.name;
        currentCharacter = p.name;
        activeCharacterEl.textContent = p.name;
        const readRes = await window.electronAPI.readPersona(p.name);
        if (readRes.success && readRes.content.trim()) {
          currentPersonaPrompt = readRes.content.trim();
        } else {
          currentPersonaPrompt = "You are a helpful assistant.";
        }
        document.body.removeChild(charOverlay);
      });

      li.appendChild(nameSpan);
      li.appendChild(loadBtn);
      charList.appendChild(li);
    });

    charBox.appendChild(charList);

    const closeCharBtn = document.createElement('button');
    closeCharBtn.textContent = 'Close';
    closeCharBtn.classList.add('close-details-btn');
    closeCharBtn.addEventListener('click', () => {
      document.body.removeChild(charOverlay);
    });
    charBox.appendChild(closeCharBtn);

    charOverlay.appendChild(charBox);
    document.body.appendChild(charOverlay);
  });

    charBox.appendChild(charList);

    const closeCharBtn = document.createElement('button');
    closeCharBtn.textContent = 'Close';
    closeCharBtn.classList.add('close-details-btn');
    closeCharBtn.addEventListener('click', () => {
      document.body.removeChild(charOverlay);
    });
    charBox.appendChild(closeCharBtn);

    charOverlay.appendChild(charBox);
    document.body.appendChild(charOverlay);

  async function populateVoiceModelSelector() {
    const result = await window.electronAPI.getVoiceModels();
    if (!result.success) {
      voiceModelSelectorContainer.textContent = 'Error loading models';
      return;
    }
    const models = result.models; // { "Name": "ID", ...}
    const customSelect = document.createElement('div');
    customSelect.classList.add('custom-select');

    const selected = document.createElement('div');
    selected.classList.add('select-selected');
    selected.textContent = '-- Select Voice Model --';
    customSelect.appendChild(selected);

    selected.addEventListener('click', () => {
      showVoiceModelSelector(models);
    });

    voiceModelSelectorContainer.innerHTML = '';
    voiceModelSelectorContainer.appendChild(customSelect);
  }

  function showVoiceModelSelector(models) {
    const overlay = document.createElement('div');
    overlay.classList.add('details-overlay');

    const box = document.createElement('div');
    box.classList.add('details-box');

    const title = document.createElement('h2');
    title.textContent = 'Select Voice Model';
    box.appendChild(title);

    const modelList = document.createElement('ul');
    modelList.style.listStyle = 'none';
    modelList.style.padding = '0';

    // "None" option
    const noneOption = document.createElement('li');
    noneOption.style.display = 'flex';
    noneOption.style.alignItems = 'center';
    noneOption.style.justifyContent = 'space-between';

    const noneNameSpan = document.createElement('span');
    noneNameSpan.textContent = 'None';
    noneOption.appendChild(noneNameSpan);

    const noneSelectBtn = document.createElement('button');
    noneSelectBtn.textContent = 'Select';
    noneSelectBtn.addEventListener('click', () => {
      const voiceModelSelector = document.querySelector('.voice-model-selector-container .custom-select .select-selected');
      if (voiceModelSelector) {
        voiceModelSelector.textContent = 'None';
        document.body.removeChild(overlay);
      }
    });
    noneOption.appendChild(noneSelectBtn);
    modelList.appendChild(noneOption);

    // Display each model
    Object.keys(models).forEach(name => {
      const li = document.createElement('li');
      li.style.display = 'flex';
      li.style.alignItems = 'center';
      li.style.justifyContent = 'space-between';

      const nameSpan = document.createElement('span');
      nameSpan.textContent = name;
      li.appendChild(nameSpan);

      const selectBtn = document.createElement('button');
      selectBtn.textContent = 'Select';
      selectBtn.addEventListener('click', () => {
        const voiceModelSelector = document.querySelector('.voice-model-selector-container .custom-select .select-selected');
        if (voiceModelSelector) {
          voiceModelSelector.textContent = name;
        }
        document.body.removeChild(overlay);
      });
      li.appendChild(selectBtn);
      modelList.appendChild(li);
    });

    box.appendChild(modelList);

    const closeBtn = document.createElement('button');
    closeBtn.textContent = 'Close';
    closeBtn.classList.add('close-details-btn');
    closeBtn.addEventListener('click', () => {
      document.body.removeChild(overlay);
    });
    box.appendChild(closeBtn);

    overlay.appendChild(box);
    document.body.appendChild(overlay);
  }

  window.populateVoiceModelSelector = populateVoiceModelSelector;
});
