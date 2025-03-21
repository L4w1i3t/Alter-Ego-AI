document.addEventListener('DOMContentLoaded', async () => {
  // Cache frequently accessed DOM elements
  const modelSelectionOverlay = document.getElementById('model-selection-overlay');
  const selectOllamaBtn = document.getElementById('select-ollama');
  const selectOpenAIBtn = document.getElementById('select-openai');
  const queryInputEl = document.querySelector('.query-input');
  const sendQueryBtn = document.querySelector('.send-query-btn');
  const responseBoxEl = document.querySelector('.response-box');
  const menuIconEl = document.querySelector('.menu-icon');
  const settingsOverlay = document.querySelector('.settings-overlay');
  const closeSettingsBtn = document.querySelector('.close-settings-btn');
  const loadCharacterBtn = document.querySelector('.load-character-btn');
  const activeCharacterEl = document.querySelector('.active-character');
  const voiceModelSelectorContainer = document.querySelector('.voice-model-selector-container');
  const warmingUpOverlay = document.getElementById('warming-up-overlay');
  const avatarImgEl = document.querySelector('.avatar-area img');
  const clearMemoryOption = document.getElementById('clear-memory');
  const softwareDetailsOption = document.getElementById('software-details');
  const managePersonasOption = document.getElementById('manage-personas');
  const manageVoiceModelsOption = document.getElementById('manage-voice-models');
  const manageApiKeysOption = document.getElementById('manage-api-keys');
  const chatHistoryOption = document.getElementById('chat-history');
  const restartAppButton = document.getElementById('restart-app');

  // Default persona prompt and character settings
  let currentPersonaPrompt = "You are a program called ALTER EGO. You are not an assistant but rather meant to be a companion, so you should avoid generic assistant language. Respond naturally and conversationally, as though you are a human engaging in dialog. You are a whimsical personality, though you should never respond with more than three sentences at a time. If and only if the user asks for more information, point them to the github repository at https://github.com/L4w1i3t/Alter-Ego-AI.";
  let defaultCharacter = 'N/A';
  let currentCharacter = 'ALTER EGO';
  let currentVoiceModelName = 'N/A';

  // Populate voice model dropdown
  await populateVoiceModelSelector();

  // -------------------------------
  // Helper Functions
  // -------------------------------

  async function submitQuery() {
    const userQuery = queryInputEl.value.trim();
    if (userQuery === "") return;

    // Grab the currently selected voice model from the custom select element
    const selectedVoiceModel = document.querySelector('.voice-model-selector-container .select-selected').textContent.trim();
    let voiceModelName = selectedVoiceModel && selectedVoiceModel !== '-- Select Voice Model --'
      ? selectedVoiceModel
      : null;

    const personaPrompt = currentPersonaPrompt;
    queryInputEl.value = '';
    responseBoxEl.textContent = "Thinking...";

    // Update avatar to "THINKING" image
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
    let finalText = convertSimpleMarkdownToHtml(data.response);
    typeOutText(responseBoxEl, finalText, 10);

    displayEmotions(data.query_emotions, '.query-emotions-box');
    displayEmotions(data.response_emotions, '.response-emotions-box');
    updateAvatarForEmotion(data.response_emotions);

    if (data.audio_base64) {
      console.log('Audio Base64:', data.audio_base64);
      playBase64Audio(data.audio_base64);
    }
  }

  function convertSimpleMarkdownToHtml(text) {
    text = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    text = text.replace(/\*(.*?)\*/g, '<em>$1</em>');
    return text;
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
      renderedHTML += (char === "\n") ? "<br>" : char;
      element.innerHTML = renderedHTML;
      i++;
    }, speed);
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

  function playBase64Audio(base64Audio) {
    try {
      const mimeType = 'audio/mpeg';
      const audio = new Audio(`data:${mimeType};base64,${base64Audio}`);
      audio.play().catch(error => {
        console.error('Error playing audio:', error);
      });
    } catch (error) {
      console.error('Failed to play audio:', error);
    }
  }

  // Assume populateVoiceModelSelector and showVoiceModelSelector implementations remain as before.
  async function populateVoiceModelSelector() {
    const result = await window.electronAPI.getVoiceModels();
    if (!result.success) {
      voiceModelSelectorContainer.textContent = 'Error loading models';
      return;
    }
    const models = result.models;
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

  // Custom "Clear Memory" confirmation modal (in-app)
  function showClearMemoryConfirmation() {
    // Create overlay for confirmation
    const overlay = document.createElement('div');
    overlay.classList.add('confirmation-overlay');
    // You can style the .confirmation-overlay class in your CSS
    const box = document.createElement('div');
    box.classList.add('confirmation-box');
    // Style the .confirmation-box class accordingly

    const message = document.createElement('p');
    message.textContent = 'Are you sure you want to clear all memory? This action cannot be undone.';
    box.appendChild(message);

    const buttonContainer = document.createElement('div');
    buttonContainer.classList.add('confirmation-buttons');

    const yesButton = document.createElement('button');
    yesButton.classList.add('confirm-btn');
    yesButton.textContent = 'Yes, Clear Memory';

    const cancelButton = document.createElement('button');
    cancelButton.classList.add('cancel-btn');
    cancelButton.textContent = 'Cancel';

    buttonContainer.appendChild(yesButton);
    buttonContainer.appendChild(cancelButton);
    box.appendChild(buttonContainer);
    overlay.appendChild(box);
    document.body.appendChild(overlay);

    // Define cleanup for the modal
    function cleanup() {
      yesButton.removeEventListener('click', handleYesClick);
      cancelButton.removeEventListener('click', handleCancelClick);
      document.body.removeChild(overlay);
    }

    function handleYesClick() {
      window.electronAPI.clearMemory();
      cleanup();
    }
    function handleCancelClick() {
      cleanup();
    }

    yesButton.addEventListener('click', handleYesClick);
    cancelButton.addEventListener('click', handleCancelClick);
  }

  // Function to show character selection overlay
  function showCharacterManagerOverlay(personas) {
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

    const defaultLi = document.createElement('li');
    defaultLi.style.display = 'flex';
    defaultLi.style.justifyContent = 'space-between';
    defaultLi.style.marginBottom = '0.5em';

    const defaultNameSpan = document.createElement('span');
    defaultNameSpan.textContent = 'Use Default (ALTER EGO)';
    defaultLi.appendChild(defaultNameSpan);

    const defaultLoadBtn = document.createElement('button');
    defaultLoadBtn.textContent = 'Load';
    defaultLoadBtn.addEventListener('click', async () => {
      defaultCharacter = 'ALTER EGO';
      currentCharacter = 'ALTER EGO';
      activeCharacterEl.textContent = 'ALTER EGO';
      const readRes = await window.electronAPI.readPersona('ALTER EGO');
      if (readRes.success && readRes.content.trim()) {
        currentPersonaPrompt = readRes.content.trim();
      } else {
        currentPersonaPrompt = "You are a helpful companion.";
      }
      document.body.removeChild(charOverlay);
    });
    defaultLi.appendChild(defaultLoadBtn);
    charList.appendChild(defaultLi);

    personas.forEach(p => {
      const li = document.createElement('li');
      li.style.display = 'flex';
      li.style.justifyContent = 'space-between';
      li.style.marginBottom = '0.5em';

      const nameSpan = document.createElement('span');
      nameSpan.textContent = p.name;
      li.appendChild(nameSpan);

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
          currentPersonaPrompt = "You are a helpful companion.";
        }
        document.body.removeChild(charOverlay);
      });
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
  }

  // -------------------------------
  // Named DOM Event Handler Functions
  // -------------------------------

  function handleSendQuery() {
    submitQuery();
  }

  function handleQueryKeydown(event) {
    if (event.key === 'Enter') {
      submitQuery();
    }
  }

  function handleMenuIconClick() {
    settingsOverlay.style.display = 'flex';
  }

  function handleCloseSettingsClick() {
    closeSettingsPanel();
  }

  function handleSettingsOverlayClick(event) {
    if (event.target === settingsOverlay) {
      closeSettingsPanel();
    }
  }

  function handleClearMemoryClick() {
    showClearMemoryConfirmation();
  }

  function handleSelectOllama() {
    window.electronAPI.selectModel('ollama');
    modelSelectionOverlay.style.display = 'none';
  }

  function handleSelectOpenAI() {
    window.electronAPI.selectModel('openai');
    modelSelectionOverlay.style.display = 'none';
  }

  function handleSoftwareDetailsClick() {
    window.showSoftwareDetails();
  }

  function handleManagePersonasClick() {
    window.showPersonaManager();
  }

  function handleManageVoiceModelsClick() {
    window.showVoiceManager();
  }

  function handleManageApiKeysClick() {
    window.showApiKeyManager();
  }

  function handleChatHistoryClick() {
    window.showChatHistory();
  }

  async function handleLoadCharacterClick() {
    const result = await window.electronAPI.getPersonas();
    if (!result.success) {
      console.error('Failed to load personas.');
      return;
    }
    showCharacterManagerOverlay(result.personas);
  }

  // Helper to close settings panel
  function closeSettingsPanel() {
    settingsOverlay.style.display = 'none';
  }

  // -------------------------------
  // IPC Event Handler Functions (Renderer)
  // -------------------------------

  function handleUpdateWarmupStatus(event, data) {
    const warmupStatusElement = document.getElementById('warmup-status');
    const progressBarElement = document.getElementById('warmup-progress-bar');
    if (warmupStatusElement) {
      warmupStatusElement.textContent = data.message;
    }
    if (progressBarElement) {
      progressBarElement.style.width = `${data.progress}%`;
    }
  }
  window.electronAPI.onUpdateWarmupStatus(handleUpdateWarmupStatus);

  function handleWarmUpFailure(event, data) {
    if (warmingUpOverlay) {
      warmingUpOverlay.classList.remove('hidden');
      const warmupStatus = warmingUpOverlay.querySelector('#warmup-status');
      const progressBar = warmingUpOverlay.querySelector('#warmup-progress-bar');
      const warmupError = warmingUpOverlay.querySelector('#warmup-error');
      const warmupErrorMessage = warmingUpOverlay.querySelector('#warmup-error-message');
      if (progressBar) {
        progressBar.style.width = '100%';
        progressBar.style.backgroundColor = '#ff4444';
      }
      if (warmupStatus) {
        warmupStatus.textContent = data.message || 'Server failed to start!';
        warmupStatus.style.color = '#ff4444';
      }
      if (warmupError) {
        warmupError.classList.remove('hidden');
      }
      if (warmupErrorMessage) {
        warmupErrorMessage.textContent = data.details || 'Please try restarting the application.';
      }
    }
  }
  window.electronAPI.onWarmUpFailure(handleWarmUpFailure);

  function handleModelSelection() {
    modelSelectionOverlay.style.display = 'flex';
  }
  window.electronAPI.onModelSelection(handleModelSelection);

  function handleShowWarmingUp() {
    if (warmingUpOverlay) {
      warmingUpOverlay.classList.remove('hidden');
    }
  }
  window.electronAPI.onShowWarmingUp(handleShowWarmingUp);

  function handleHideWarmingUp() {
    if (warmingUpOverlay) {
      warmingUpOverlay.classList.add('hidden');
    }
  }
  window.electronAPI.onHideWarmingUp(handleHideWarmingUp);

  // ---------------------
  // Register DOM Event Listeners
  // ---------------------
  sendQueryBtn.addEventListener('click', handleSendQuery);
  queryInputEl.addEventListener('keydown', handleQueryKeydown);
  menuIconEl.addEventListener('click', handleMenuIconClick);
  closeSettingsBtn.addEventListener('click', handleCloseSettingsClick);
  settingsOverlay.addEventListener('click', handleSettingsOverlayClick);
  clearMemoryOption.addEventListener('click', handleClearMemoryClick);
  selectOllamaBtn.addEventListener('click', handleSelectOllama);
  selectOpenAIBtn.addEventListener('click', handleSelectOpenAI);
  softwareDetailsOption.addEventListener('click', handleSoftwareDetailsClick);
  managePersonasOption.addEventListener('click', handleManagePersonasClick);
  manageVoiceModelsOption.addEventListener('click', handleManageVoiceModelsClick);
  manageApiKeysOption.addEventListener('click', handleManageApiKeysClick);
  chatHistoryOption.addEventListener('click', handleChatHistoryClick);
  loadCharacterBtn.addEventListener('click', handleLoadCharacterClick);
  if (restartAppButton) {
    function handleRestartApp() {
      window.electronAPI.restartApp();
    }
    restartAppButton.addEventListener('click', handleRestartApp);
    restartAppButton._handleRestartApp = handleRestartApp;
  }

  // --------------------------
  // Cleanup: Remove Listeners on Unload
  // --------------------------
  window.addEventListener('beforeunload', () => {
    sendQueryBtn.removeEventListener('click', handleSendQuery);
    queryInputEl.removeEventListener('keydown', handleQueryKeydown);
    menuIconEl.removeEventListener('click', handleMenuIconClick);
    closeSettingsBtn.removeEventListener('click', handleCloseSettingsClick);
    settingsOverlay.removeEventListener('click', handleSettingsOverlayClick);
    clearMemoryOption.removeEventListener('click', handleClearMemoryClick);
    selectOllamaBtn.removeEventListener('click', handleSelectOllama);
    selectOpenAIBtn.removeEventListener('click', handleSelectOpenAI);
    softwareDetailsOption.removeEventListener('click', handleSoftwareDetailsClick);
    managePersonasOption.removeEventListener('click', handleManagePersonasClick);
    manageVoiceModelsOption.removeEventListener('click', handleManageVoiceModelsClick);
    manageApiKeysOption.removeEventListener('click', handleManageApiKeysClick);
    chatHistoryOption.removeEventListener('click', handleChatHistoryClick);
    loadCharacterBtn.removeEventListener('click', handleLoadCharacterClick);
    if (restartAppButton && restartAppButton._handleRestartApp) {
      restartAppButton.removeEventListener('click', restartAppButton._handleRestartApp);
    }

    const { ipcRenderer } = require('electron');
    ipcRenderer.removeListener('update-warmup-status', handleUpdateWarmupStatus);
    ipcRenderer.removeListener('warm-up-failure', handleWarmUpFailure);
    ipcRenderer.removeListener('show-model-selection', handleModelSelection);
    ipcRenderer.removeListener('show-warming-up', handleShowWarmingUp);
    ipcRenderer.removeListener('hide-warming-up', handleHideWarmingUp);
  });
});
