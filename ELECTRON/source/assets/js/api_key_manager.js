// api_key_manager.js
async function showApiKeyManager() {
  const result = await window.electronAPI.getApiKeys();
  if (!result.success) {
    console.error('Failed to load API keys.');
    return;
  }

  const keys = result.keys; // e.g. { "ELEVENLABS_API_KEY": "..." }

  // Create the dark overlay
  const overlay = document.createElement('div');
  overlay.classList.add('details-overlay');

  // Create the main box
  const box = document.createElement('div');
  box.classList.add('details-box');
  box.classList.add('api-keys-box');

  // Title
  const title = document.createElement('h2');
  title.textContent = 'Manage API Keys';
  box.appendChild(title);

  // Brief instructions
  const instructions = document.createElement('p');
  instructions.textContent =
    'View, copy, or edit your API keys here. Changes require restart.';
  box.appendChild(instructions);

  // Container for the list of keys
  const keyListContainer = document.createElement('div');
  keyListContainer.classList.add('api-key-list-container');

  // For each key in `keys`, excluding OpenAI keys
  Object.keys(keys).forEach((keyName) => {
    if (keyName === 'OPENAI_API_KEY') return;
    const keyValue = keys[keyName];

    const card = document.createElement('div');
    card.classList.add('api-key-card');

    const nameSpan = document.createElement('span');
    nameSpan.classList.add('api-key-card-name');
    nameSpan.textContent = keyName + ':';
    card.appendChild(nameSpan);

    let showingFull = false;
    const maskedKey = maskKey(keyValue);
    const keySpan = document.createElement('span');
    keySpan.classList.add('api-key-card-key');
    keySpan.textContent = maskedKey;
    card.appendChild(keySpan);

    const buttonGroup = document.createElement('div');
    buttonGroup.classList.add('api-key-card-buttons');

    const toggleBtn = document.createElement('button');
    toggleBtn.classList.add('api-key-card-button');
    toggleBtn.textContent = 'Show';
    toggleBtn.addEventListener('click', () => {
      showingFull = !showingFull;
      if (showingFull) {
        keySpan.textContent = keyValue;
        toggleBtn.textContent = 'Hide';
      } else {
        keySpan.textContent = maskedKey;
        toggleBtn.textContent = 'Show';
      }
    });
    buttonGroup.appendChild(toggleBtn);

    const copyBtn = document.createElement('button');
    copyBtn.classList.add('api-key-card-button');
    copyBtn.textContent = 'Copy';
    copyBtn.addEventListener('click', () => {
      const textToCopy = showingFull ? keyValue : maskedKey;
      navigator.clipboard.writeText(textToCopy).then(() => {
        console.log('API key copied to clipboard.');
      });
    });
    buttonGroup.appendChild(copyBtn);

    const editBtn = document.createElement('button');
    editBtn.classList.add('api-key-card-button');
    editBtn.textContent = 'Edit';
    editBtn.addEventListener('click', () => {
      editApiKey(keyName, keyValue);
    });
    buttonGroup.appendChild(editBtn);

    card.appendChild(buttonGroup);
    keyListContainer.appendChild(card);
  });

  box.appendChild(keyListContainer);

  const closeBtn = document.createElement('button');
  closeBtn.textContent = 'Close';
  closeBtn.classList.add('close-details-btn');
  closeBtn.addEventListener('click', () => {
    document.body.removeChild(overlay);
  });
  box.appendChild(closeBtn);

  overlay.appendChild(box);
  document.body.appendChild(overlay);

  function maskKey(key) {
    if (key.length <= 10) {
      return key[0] + '...' + key[key.length - 1];
    }
    const start = key.slice(0, 5);
    const end = key.slice(-5);
    return start + '...' + end;
  }

  async function editApiKey(keyName, oldValue) {
    const formOverlay = document.createElement('div');
    formOverlay.classList.add('details-overlay');

    const formBox = document.createElement('div');
    formBox.classList.add('details-box');
    formBox.classList.add('api-key-edit-box');

    const formTitle = document.createElement('h2');
    formTitle.textContent = `Edit ${keyName}`;
    formBox.appendChild(formTitle);

    const inputLabel = document.createElement('label');
    inputLabel.style.display = 'block';
    inputLabel.style.marginBottom = '0.5em';
    inputLabel.textContent = 'Enter new value:';
    formBox.appendChild(inputLabel);

    const input = document.createElement('input');
    input.type = 'text';
    input.value = oldValue;
    input.style.width = '100%';
    input.style.marginBottom = '1em';
    formBox.appendChild(input);

    const buttonsRow = document.createElement('div');
    buttonsRow.style.display = 'flex';
    buttonsRow.style.justifyContent = 'flex-end';
    buttonsRow.style.gap = '1em';

    const saveBtn = document.createElement('button');
    saveBtn.textContent = 'Save Changes';
    saveBtn.addEventListener('click', async () => {
      const newKeyValue = input.value.trim();
      if (!newKeyValue) {
        console.log('API Key cannot be empty.');
        return;
      }
      const res = await window.electronAPI.updateApiKey({ keyName, newKeyValue });
      if (res.success) {
        console.log('API Key updated successfully.');
        document.body.removeChild(formOverlay);
        document.body.removeChild(overlay);
        showApiKeyManager();
        showRestartNotification();
      } else {
        console.error(res.message);
      }
    });
    buttonsRow.appendChild(saveBtn);

    const cancelBtn = document.createElement('button');
    cancelBtn.textContent = 'Cancel';
    cancelBtn.addEventListener('click', () => {
      document.body.removeChild(formOverlay);
    });
    buttonsRow.appendChild(cancelBtn);

    formBox.appendChild(buttonsRow);

    formOverlay.appendChild(formBox);
    document.body.appendChild(formOverlay);
  }

  function showRestartNotification() {
    const notificationOverlay = document.createElement('div');
    notificationOverlay.classList.add('details-overlay');

    const notificationBox = document.createElement('div');
    notificationBox.classList.add('details-box');

    const notificationTitle = document.createElement('h2');
    notificationTitle.textContent = 'Restart Required';
    notificationBox.appendChild(notificationTitle);

    const notificationMessage = document.createElement('p');
    notificationMessage.textContent =
      'API Key change detected. You must restart the program for changes to take effect.';
    notificationBox.appendChild(notificationMessage);

    const closeNotificationBtn = document.createElement('button');
    closeNotificationBtn.textContent = 'Close';
    closeNotificationBtn.classList.add('close-details-btn');
    closeNotificationBtn.addEventListener('click', () => {
      document.body.removeChild(notificationOverlay);
    });
    notificationBox.appendChild(closeNotificationBtn);

    notificationOverlay.appendChild(notificationBox);
    document.body.appendChild(notificationOverlay);
  }
}

window.showApiKeyManager = showApiKeyManager;
