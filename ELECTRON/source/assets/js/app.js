// app.js (Modified: Removed TTS/Voice Model functionality and obscured voice model selector)

document.addEventListener('DOMContentLoaded', async () => {
  // ---------- DOM Elements ----------
  const queryInputEl = document.querySelector('.query-input');
  const sendQueryBtn = document.querySelector('.send-query-btn');
  const menuIconEl = document.querySelector('.menu-icon');
  const settingsOverlay = document.querySelector('.settings-overlay');
  const closeSettingsBtn = document.querySelector('.close-settings-btn');
  const loadCharacterBtn = document.querySelector('.load-character-btn');
  const activeCharacterEl = document.querySelector('.active-character');
  const voiceModelSelectorContainer = document.querySelector('.voice-model-selector-container');
  const warmingUpOverlay = document.getElementById('warming-up-overlay');
  const responseBoxEl = document.querySelector('.response-box');
  const avatarImgEl = document.querySelector('.avatar-area img');

  // Optional emotion boxes
  const queryEmotionsBox = document.querySelector('.query-emotions-box');
  const responseEmotionsBox = document.querySelector('.response-emotions-box');

  // Persona state (Voice model functionality removed)
  let currentPersonaPrompt = "You are a program called ALTER EGO. You are not an assistant but rather meant to be a companion, so you should avoid generic assistant language. Respond naturally and conversationally, as though you are a human engaging in dialog. You are a whimsical personality, though you should never respond with more than three sentences at a time. If and only if the user asks for more information, point them to the github repository at https://github.com/L4w1i3t/Alter-Ego-AI.";
  let defaultCharacter = 'N/A';
  let currentCharacter = 'ALTER EGO';

  // Hide the voice model selector UI for now.
  if (voiceModelSelectorContainer) {
    voiceModelSelectorContainer.style.display = 'none';
  }

  // ---------- UTILITY FUNCTIONS FOR EMOTIONS ----------
  function displayEmotions(container, predictions) {
    container.innerHTML = "";
    if (!predictions || !predictions.length) return;
    const sorted = [...predictions].sort((a, b) => b.score - a.score);
    sorted.forEach(item => {
      const p = document.createElement("p");
      p.textContent = `${item.label}: ${item.score.toFixed(3)}`;
      container.appendChild(p);
    });
  }
  
  function getTopEmotion(predictions) {
    if (!predictions || predictions.length === 0) return null;
    const sorted = [...predictions].sort((a, b) => b.score - a.score);
    return sorted[0].label;
  }
  
  function setAvatarToEmotion(emotionLabel) {
    const avatarImgEl = document.querySelector('.avatar-area img');
    const EMOTION_SPRITES = {
      admiration: "admiration.png",
      amusement: "amusement.png",
      anger: "anger.png",
      annoyance: "annoyance.png",
      approval: "approval.png",
      caring: "caring.png",
      confusion: "confusion.png",
      curiosity: "curiosity.png",
      desire: "desire.png",
      disappointment: "disappointment.png",
      disapproval: "disapproval.png",
      disgust: "disgust.png",
      embarrassment: "embarrassment.png",
      excitement: "excitement.png",
      fear: "fear.png",
      gratitude: "gratitude.png",
      grief: "grief.png",
      joy: "joy.png",
      love: "love.png",
      nervousness: "nervousness.png",
      neutral: "neutral.png",
      optimism: "optimism.png",
      pride: "pride.png",
      realization: "realization.png",
      relief: "relief.png",
      remorse: "remorse.png",
      sadness: "sadness.png",
      surprise: "surprise.png",
      THINKING: "THINKING.png",
    };
   
    if (!emotionLabel || !EMOTION_SPRITES[emotionLabel]) {
      avatarImgEl.src = 'persistentdata/avatars/DEFAULT/neutral.png';
      return;
    }
    avatarImgEl.src = `persistentdata/avatars/DEFAULT/${EMOTION_SPRITES[emotionLabel]}`;
  }
  
  async function detectAndShowEmotions(text) {
    if (!text.trim()) {
      setAvatarToEmotion('neutral');
      return;
    }
    const results = await window.electronAPI.detectEmotions([text]);
    if (!results || !results[0] || results[0].length === 0) {
      responseEmotionsBox.innerHTML = '';
      setAvatarToEmotion('neutral');
      return;
    }
    const emotionArray = results[0];
    displayEmotions(responseEmotionsBox, emotionArray);
    const topEmotion = getTopEmotion(emotionArray);
    setAvatarToEmotion(topEmotion);
  }
  
  // ---------- NEW: Typing Animation for Once-Approach ----------
  // Immediately after receiving the full answer, run emotion detection so sprite changes appear as typing begins.
  function animateTyping(fullText) {
    // Run emotion detection on the full answer right away
    detectAndShowEmotions(fullText);
   
    responseBoxEl.innerHTML = "";
    let index = 0;
    const interval = setInterval(() => {
      if (index < fullText.length) {
        responseBoxEl.innerHTML = marked.parse(fullText.substring(0, index + 1));
        index++;
      } else {
        clearInterval(interval);
      }
    }, 8);
  }
  
  // ---------- Submitting a Query ----------
  sendQueryBtn.addEventListener('click', submitQuery);
  queryInputEl.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
      submitQuery();
    }
  });
  
  async function submitQuery() {
    const userQuery = queryInputEl.value.trim();
    if (!userQuery) return;
   
    // Clear input and reset display
    queryInputEl.value = '';
    responseBoxEl.textContent = "Thinking...";
    if (avatarImgEl) {
      avatarImgEl.src = 'persistentdata/avatars/DEFAULT/THINKING.png';
    }
   
    // Immediately detect and display user emotions
    const [userEmotions] = await window.electronAPI.detectEmotions([userQuery]);
    if (userEmotions) {
      displayEmotions(queryEmotionsBox, userEmotions);
    } else {
      queryEmotionsBox.innerHTML = '';
    }
   
    try {
      // Removed voice model parameter from query
      const responseObj = await window.electronAPI.queryOllama({
        query: userQuery,
        persona_name: currentCharacter,
        persona_prompt: currentPersonaPrompt
      });
      const answer = responseObj.response;
      
      // Begin typing animation of the answer.
      animateTyping(answer);
      
      // Removed audio playback (TTS) section.
    } catch (err) {
      responseBoxEl.textContent = `Error: ${err.message}`;
    }
  }
  
  // ---------- Settings Panel, Clear Memory, etc. ----------
  menuIconEl.addEventListener('click', () => {
    settingsOverlay.style.display = 'flex';
  });
  closeSettingsBtn.addEventListener('click', closeSettingsPanel);
  settingsOverlay.addEventListener('click', (event) => {
    if (event.target === settingsOverlay) {
      closeSettingsPanel();
    }
  });
  function closeSettingsPanel() {
    settingsOverlay.style.display = 'none';
  }
  
  const clearMemoryOption = document.getElementById('clear-memory');
  clearMemoryOption.addEventListener('click', showClearMemoryConfirmation);
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
  window.electronAPI.onClearMemoryResult((event, data) => {
    console.log('Memory clearing result:', data);
  });
  
  const softwareDetailsOption = document.getElementById('software-details');
  if (softwareDetailsOption) {
    softwareDetailsOption.addEventListener('click', () => {
      window.showSoftwareDetails();
    });
  }
  const managePersonasOption = document.getElementById('manage-personas');
  if (managePersonasOption) {
    managePersonasOption.addEventListener('click', () => {
      window.showPersonaManager();
    });
  }
  const apiKeysOption = document.getElementById('manage-api-keys');
  if (apiKeysOption) {
    apiKeysOption.addEventListener('click', () => {
      window.showApiKeyManager();
    });
  }
  // Removed voice models management option
  const chatHistoryOption = document.getElementById('chat-history');
  if (chatHistoryOption) {
    chatHistoryOption.addEventListener('click', () => {
      window.showChatHistory();
    });
  }
  
  // Warming up events
  window.electronAPI.onShowWarmingUp(() => {
    if (warmingUpOverlay) warmingUpOverlay.classList.remove('hidden');
  });
  window.electronAPI.onHideWarmingUp(() => {
    if (warmingUpOverlay) warmingUpOverlay.classList.add('hidden');
  });
  window.electronAPI.onWarmUpFailure(() => {
    showServerFailedOverlay();
  });
  function showServerFailedOverlay() {
    if (warmingUpOverlay) {
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
  
  // ---------- Persona Loading Logic ----------
  loadCharacterBtn.addEventListener('click', async () => {
    const result = await window.electronAPI.getPersonas();
    if (!result.success) {
      console.error('Failed to load personas.');
      return;
    }
    const personas = result.personas;
  
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
  
    // Default (ALTER EGO)
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
      currentPersonaPrompt =
        "You are a program called ALTER EGO. You are not an assistant but rather meant to be a companion, so you should avoid generic assistant language. Respond naturally and conversationally, as though you are a human engaging in dialog. You are a whimsical personality, though you should never respond with more than three sentences at a time. If and only if the user asks for more information, point them to the github repository at https://github.com/L4w1i3t/Alter-Ego-AI.";
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
          currentPersonaPrompt = "You are a program called ALTER EGO. You are not an assistant but rather meant to be a companion, so you should avoid generic assistant language. Respond naturally and conversationally, as though you are a human engaging in dialog. You are a whimsical personality, though you should never respond with more than three sentences at a time. If and only if the user asks for more information, point them to the github repository at https://github.com/L4w1i3t/Alter-Ego-AI.";
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
  });
});
