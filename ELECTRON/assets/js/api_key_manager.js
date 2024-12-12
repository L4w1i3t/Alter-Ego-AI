async function showApiKeyManager() {
    const result = await window.electronAPI.getApiKeys();
    if (!result.success) {
      alert('Failed to load API keys.');
      return;
    }
  
    const keys = result.keys; // { "OPENAI_API_KEY": "sk-...", "ELEVENLABS_API_KEY": "sk-..." }
  
    // Create overlay
    const overlay = document.createElement('div');
    overlay.classList.add('details-overlay');
  
    // Create box
    const box = document.createElement('div');
    box.classList.add('details-box');
  
    const title = document.createElement('h2');
    title.textContent = 'Manage API Keys';
    box.appendChild(title);
  
    const keyList = document.createElement('ul');
    keyList.style.listStyle = 'none';
    keyList.style.padding = '0';
  
    Object.keys(keys).forEach(keyName => {
      const keyValue = keys[keyName];
  
      const li = document.createElement('li');
      li.style.display = 'flex';
      li.style.alignItems = 'center';
      li.style.justifyContent = 'space-between';
      li.style.marginBottom = '0.5em';
  
      // Container for the key display
      const keyContainer = document.createElement('div');
      keyContainer.style.display = 'flex';
      keyContainer.style.alignItems = 'center';
      keyContainer.style.gap = '1em';
  
      const nameSpan = document.createElement('span');
      nameSpan.style.flexShrink = '0';
      nameSpan.textContent = keyName + ':';
  
      // Mask the key: show first 5 chars and last 5 chars only
      const maskedKey = maskKey(keyValue);
      let showingFull = false;
  
      const keySpan = document.createElement('span');
      keySpan.style.whiteSpace = 'nowrap';
      keySpan.textContent = maskedKey;
  
      const toggleBtn = document.createElement('button');
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
  
      keyContainer.appendChild(nameSpan);
      keyContainer.appendChild(keySpan);
      keyContainer.appendChild(toggleBtn);
  
      li.appendChild(keyContainer);
  
      // Edit button
      const editBtn = document.createElement('button');
      editBtn.textContent = 'Edit';
      editBtn.addEventListener('click', () => {
        editApiKey(keyName, keyValue);
      });
      li.appendChild(editBtn);
  
      keyList.appendChild(li);
    });
  
    box.appendChild(keyList);
  
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
  
    function maskKey(key) {
      if (key.length <= 10) {
        // If very short, just partially mask
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
  
      const formTitle = document.createElement('h2');
      formTitle.textContent = `Edit ${keyName}`;
      formBox.appendChild(formTitle);
  
      const input = document.createElement('input');
      input.type = 'text';
      input.value = oldValue;
      input.style.width = '100%';
      input.style.marginBottom = '1em';
      formBox.appendChild(input);
  
      const saveBtn = document.createElement('button');
      saveBtn.textContent = 'Save Changes';
      saveBtn.style.marginTop = '1em';
      saveBtn.addEventListener('click', async () => {
        const newKeyValue = input.value.trim();
        if (!newKeyValue) {
          alert('API Key cannot be empty.');
          return;
        }
        const res = await window.electronAPI.updateApiKey({ keyName, newKeyValue });
        if (res.success) {
          alert('API Key updated successfully.');
          document.body.removeChild(formOverlay);
          document.body.removeChild(overlay);
          showApiKeyManager(); // Refresh list
        } else {
          alert(res.message);
        }
      });
      formBox.appendChild(saveBtn);
  
      const cancelBtn = document.createElement('button');
      cancelBtn.textContent = 'Cancel';
      cancelBtn.style.marginLeft = '1em';
      cancelBtn.addEventListener('click', () => {
        document.body.removeChild(formOverlay);
      });
      formBox.appendChild(cancelBtn);
  
      formOverlay.appendChild(formBox);
      document.body.appendChild(formOverlay);
    }
  }
  
  // Expose showApiKeyManager globally
  window.showApiKeyManager = showApiKeyManager;
  