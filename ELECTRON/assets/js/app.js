document.addEventListener('DOMContentLoaded', async () => {
  const srStatusEl = document.querySelector('.sr-status');
  const queryInputEl = document.querySelector('.query-input');
  const sendQueryBtn = document.querySelector('.send-query-btn');
  const menuIconEl = document.querySelector('.menu-icon');
  const settingsOverlay = document.querySelector('.settings-overlay');
  const closeSettingsBtn = document.querySelector('.close-settings-btn');
  const loadCharacterBtn = document.querySelector('.load-character-btn');
  const activeCharacterEl = document.querySelector('.active-character');
  const voiceModelSelectorContainer = document.querySelector('.voice-model-selector-container');

  let currentPersonaPrompt = "You are the secretary/guide of a program called ALTER EGO, and you are the default character data option (NOT a digital assistant). Your character merely serves as the default option for character data. If asked for help about the program, you refer the user to this link: https://github.com/L4w1i3t/Alter-Ego-AI. Your tone should be professional and straightforward/non-conversational. You should never end your sentences with an exclamation point unless it is a not-operator."; // default persona

  // Initial state of speech recognition
  let srOn = false; // currently OFF (red)
  // Current selected character and voice model
  let currentCharacter = 'N/A';
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

  async function submitQuery() {
    const queryInputEl = document.querySelector('.query-input');
    const responseBoxEl = document.querySelector('.response-box');
  
    const userQuery = queryInputEl.value.trim();
    if (userQuery === "") return;
  
    const selectedVoiceModel = document.querySelector('.voice-model-selector-container .select-selected').textContent.trim();
    let voiceModelName = selectedVoiceModel;
    // If the user never selected a voice model, set this to null or empty
    if (!voiceModelName || voiceModelName === '-- Select Voice Model --') {
      voiceModelName = null;  // or use "" if you prefer
    }
  
    const personaPrompt = currentPersonaPrompt;
  
    queryInputEl.value = '';
    responseBoxEl.textContent = "Thinking...";
  
    const response = await fetch('http://localhost:5000/query', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ 
        query: userQuery,
        persona_prompt: personaPrompt,
        voice_model_name: voiceModelName 
      })
    });
  
    const data = await response.json();
  
    // Display the assistant's text response
    const finalText = data.response;
    typeOutText(responseBoxEl, finalText, 10);
  
    // Display Emotions
    displayEmotions(data.query_emotions, '.query-emotions-box');
    displayEmotions(data.response_emotions, '.response-emotions-box');
  
    // Update Avatar
    updateAvatarForEmotion(data.response_emotions);
  
    // Play the returned audio if present
    if (data.audio_base64) {
      const audioData = data.audio_base64;
      playBase64Audio(audioData);
    }
  }  
  
  function displayEmotions(emotionsObj, selector) {
    const boxEl = document.querySelector(selector);
    boxEl.innerHTML = ''; // Clear previous content
    if (!emotionsObj || Object.keys(emotionsObj).length === 0) {
      boxEl.textContent = 'No significant emotions detected.';
      return;
    }
  
    // Let's just list the top 3 emotions if available
    const topEmotions = Object.entries(emotionsObj).slice(0, 3);
    topEmotions.forEach(([emotion, score]) => {
      const p = document.createElement('p');
      p.textContent = `${emotion}: ${(score * 100).toFixed(2)}%`;
      boxEl.appendChild(p);
    });
  }
  
  function updateAvatarForEmotion(emotionsObj) {
    const avatarImgEl = document.querySelector('.avatar-area img');
  
    if (!emotionsObj || Object.keys(emotionsObj).length === 0) {
      // No significant emotions detected, default to neutral
      avatarImgEl.src = 'persistentdata/avatars/DEFAULT/neutral.png';
      return;
    }
  
    // emotionsObj is sorted by score descending in our backend or after we slice it
    // But if we didn't ensure sorting in the backend, we rely on topEmotions logic in displayEmotions
    // Let's just get the top emotion from the object keys (assuming sorted)
    
    // Convert emotionsObj to array and find the highest score
    const topEmotion = Object.entries(emotionsObj).sort((a, b) => b[1] - a[1])[0][0];
  
    // Set the avatar image
    // Emotion filenames match the keys (e.g., joy -> joy.png)
    const emotionFilename = topEmotion.toLowerCase() + '.png';
    avatarImgEl.src = `persistentdata/avatars/DEFAULT/${emotionFilename}`;
  }  

  function typeOutText(element, text, speed) {
    element.textContent = ''; // Clear any existing text
    let i = 0;
    
    const intervalId = setInterval(() => {
      // Add next character
      element.textContent += text.charAt(i);
      i++;
  
      // If we've reached the end, clear interval
      if (i >= text.length) {
        clearInterval(intervalId);
      }
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

  // Confirmation and result dialogs for clear memory already implemented previously
  const clearMemoryOption = document.getElementById('clear-memory');
  clearMemoryOption.addEventListener('click', () => {
    showConfirmationDialog();
  });

  function showConfirmationDialog() {
    const confirmationOverlay = document.createElement('div');
    confirmationOverlay.classList.add('confirmation-overlay');

    const confirmationBox = document.createElement('div');
    confirmationBox.classList.add('confirmation-box');

    const message = document.createElement('p');
    message.textContent = 'Are you sure you want to clear all memory? This action cannot be undone.';

    const buttonsDiv = document.createElement('div');
    buttonsDiv.classList.add('confirmation-buttons');

    const confirmBtn = document.createElement('button');
    confirmBtn.textContent = 'Yes';
    confirmBtn.classList.add('confirm-btn');

    const cancelBtn = document.createElement('button');
    cancelBtn.textContent = 'No';
    cancelBtn.classList.add('cancel-btn');

    buttonsDiv.appendChild(confirmBtn);
    buttonsDiv.appendChild(cancelBtn);

    confirmationBox.appendChild(message);
    confirmationBox.appendChild(buttonsDiv);
    confirmationOverlay.appendChild(confirmationBox);
    document.body.appendChild(confirmationOverlay);

    confirmBtn.addEventListener('click', () => {
      window.electronAPI.clearMemory();
      document.body.removeChild(confirmationOverlay);
    });

    cancelBtn.addEventListener('click', () => {
      document.body.removeChild(confirmationOverlay);
    });
  }

  window.electronAPI.onClearMemoryResult((event, data) => {
    showResultDialog(data.success, data.message);
  });

  function showResultDialog(success, message) {
    const resultOverlay = document.createElement('div');
    resultOverlay.classList.add('result-overlay');

    const resultBox = document.createElement('div');
    resultBox.classList.add('result-box');

    const resultMessage = document.createElement('p');
    resultMessage.textContent = message;
    resultMessage.style.color = success ? '#0f0' : 'red';

    const closeBtn = document.createElement('button');
    closeBtn.textContent = 'OK';
    closeBtn.classList.add('close-result-btn');

    resultBox.appendChild(resultMessage);
    resultBox.appendChild(closeBtn);
    resultOverlay.appendChild(resultBox);
    document.body.appendChild(resultOverlay);

    closeBtn.addEventListener('click', () => {
      document.body.removeChild(resultOverlay);
    });
  }

  const softwareDetailsOption = document.getElementById('software-details');
  softwareDetailsOption.addEventListener('click', () => {
    showSoftwareDetails();
  });

  // Manage Personas, Voice Models, and API Keys are already handled
  // We just add the event listeners here:
  const managePersonasOption = document.getElementById('manage-personas');
  managePersonasOption.addEventListener('click', () => {
    window.showPersonaManager();
  });

  const manageVoiceModelsOption = document.getElementById('manage-voice-models');
  manageVoiceModelsOption.addEventListener('click', () => {
    window.showVoiceManager();
  });

  const manageApiKeysOption = document.getElementById('manage-api-keys');
  manageApiKeysOption.addEventListener('click', () => {
    window.showApiKeyManager();
  });

  // Load Character functionality
  // In app.js where the loadCharacterBtn is handled:
  loadCharacterBtn.addEventListener('click', async () => {
    const result = await window.electronAPI.getPersonas();
    if (!result.success) {
      alert('Failed to load personas.');
      return;
    }

    const personas = result.personas; // {name: '...', ...}

    // Show a modal with a list of available .chr files
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
        currentCharacter = p.name;
        activeCharacterEl.textContent = p.name;

        // Read the persona's content to use as system_prompt
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


  async function populateVoiceModelSelector() {
  const result = await window.electronAPI.getVoiceModels();
  if (!result.success) {
    voiceModelSelectorContainer.textContent = 'Error loading models';
    return;
  }

  const models = result.models; // { "Name": "ID", ...}

  // Create custom select element
  const customSelect = document.createElement('div');
  customSelect.classList.add('custom-select');

  const selected = document.createElement('div');
  selected.classList.add('select-selected');
  selected.textContent = '-- Select Voice Model --';
  customSelect.appendChild(selected);

  // Add click event to open modal-style selector
  selected.addEventListener('click', () => {
    showVoiceModelSelector(models);
  });

  voiceModelSelectorContainer.innerHTML = ''; // Clear previous content
  voiceModelSelectorContainer.appendChild(customSelect);
}

function showVoiceModelSelector(models) {
  // Create overlay
  const overlay = document.createElement('div');
  overlay.classList.add('details-overlay');

  // Create box
  const box = document.createElement('div');
  box.classList.add('details-box');

  const title = document.createElement('h2');
  title.textContent = 'Select Voice Model';
  box.appendChild(title);

  const modelList = document.createElement('ul');
  modelList.style.listStyle = 'none';
  modelList.style.padding = '0';

  // Display each model
  Object.keys(models).forEach(name => {
    const li = document.createElement('li');
    li.style.display = 'flex';
    li.style.alignItems = 'center';
    li.style.justifyContent = 'space-between';

    const nameSpan = document.createElement('span');
    nameSpan.textContent = `${name}: ${models[name]}`;
    li.appendChild(nameSpan);

    // Select button
    const selectBtn = document.createElement('button');
    selectBtn.textContent = 'Select';
    selectBtn.addEventListener('click', () => {
      // Update the voice model selector in the footer
      const voiceModelSelector = document.querySelector('.voice-model-selector-container .custom-select .select-selected');
      if (voiceModelSelector) {
        voiceModelSelector.textContent = name;
        
        // Update the current voice model name in the app
        const appScript = document.querySelector('script[src="assets/js/app.js"]');
        if (appScript && appScript.contentWindow) {
          appScript.contentWindow.currentVoiceModelName = name;
        }
      }
      
      document.body.removeChild(overlay);
    });
    li.appendChild(selectBtn);

    modelList.appendChild(li);
  });

  box.appendChild(modelList);

  // Close button
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

// Expose the function globally
window.populateVoiceModelSelector = populateVoiceModelSelector;

});