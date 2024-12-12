async function showVoiceManager() {
    const result = await window.electronAPI.getVoiceModels();
    if (!result.success) {
      alert('Failed to load voice models.');
      return;
    }
  
    const models = result.models; // { "Name": "ID", ... }
  
    // Create overlay
    const overlay = document.createElement('div');
    overlay.classList.add('details-overlay');
  
    // Create box
    const box = document.createElement('div');
    box.classList.add('details-box');
  
    const title = document.createElement('h2');
    title.textContent = 'Manage Voice Models';
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
  
      // Edit button
      const editBtn = document.createElement('button');
      editBtn.textContent = 'Edit';
      editBtn.addEventListener('click', () => {
        editVoiceModel(name, models[name]);
      });
      li.appendChild(editBtn);
  
      // Delete button
      const delBtn = document.createElement('button');
      delBtn.textContent = 'Delete';
      delBtn.addEventListener('click', () => {
        deleteVoiceModel(name);
      });
      li.appendChild(delBtn);
  
      modelList.appendChild(li);
    });
  
    box.appendChild(modelList);
  
    // Add Voice Model button
    const addBtn = document.createElement('button');
    addBtn.textContent = 'Add Voice Model';
    addBtn.style.display = 'block';
    addBtn.style.margin = '1em auto';
    addBtn.addEventListener('click', () => {
      addVoiceModelForm();
    });
    box.appendChild(addBtn);
  
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
  
    async function addVoiceModelForm() {
      const formOverlay = document.createElement('div');
      formOverlay.classList.add('details-overlay');
  
      const formBox = document.createElement('div');
      formBox.classList.add('details-box');
  
      const formTitle = document.createElement('h2');
      formTitle.textContent = 'Add New Voice Model';
      formBox.appendChild(formTitle);
  
      const nameInput = document.createElement('input');
      nameInput.type = 'text';
      nameInput.placeholder = 'Voice model name';
      nameInput.style.width = '100%';
      nameInput.style.marginBottom = '1em';
      formBox.appendChild(nameInput);
  
      const idInput = document.createElement('input');
      idInput.type = 'text';
      idInput.placeholder = 'Voice model ID';
      idInput.style.width = '100%';
      idInput.style.marginBottom = '1em';
      formBox.appendChild(idInput);
  
      const saveBtn = document.createElement('button');
      saveBtn.textContent = 'Save';
      saveBtn.style.marginTop = '1em';
      saveBtn.addEventListener('click', async () => {
        const name = nameInput.value.trim();
        const id = idInput.value.trim();
        if (!name || !id) {
          alert('Name and ID cannot be empty.');
          return;
        }
        const res = await window.electronAPI.addVoiceModel({ name, id });
        if (res.success) {
          alert('Voice model added successfully.');
          document.body.removeChild(formOverlay);
          document.body.removeChild(overlay);
          showVoiceManager(); // Refresh the list
          window.populateVoiceModelSelector();
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
  
    async function editVoiceModel(oldName, oldId) {
      const formOverlay = document.createElement('div');
      formOverlay.classList.add('details-overlay');
  
      const formBox = document.createElement('div');
      formBox.classList.add('details-box');
  
      const formTitle = document.createElement('h2');
      formTitle.textContent = `Edit Voice Model (${oldName})`;
      formBox.appendChild(formTitle);
  
      const nameInput = document.createElement('input');
      nameInput.type = 'text';
      nameInput.value = oldName;
      nameInput.style.width = '100%';
      nameInput.style.marginBottom = '1em';
      formBox.appendChild(nameInput);
  
      const idInput = document.createElement('input');
      idInput.type = 'text';
      idInput.value = oldId;
      idInput.style.width = '100%';
      idInput.style.marginBottom = '1em';
      formBox.appendChild(idInput);
  
      const saveBtn = document.createElement('button');
      saveBtn.textContent = 'Save Changes';
      saveBtn.style.marginTop = '1em';
      saveBtn.addEventListener('click', async () => {
        const newName = nameInput.value.trim();
        const newId = idInput.value.trim();
        if (!newName || !newId) {
          alert('Name and ID cannot be empty.');
          return;
        }
        const res = await window.electronAPI.updateVoiceModel({ oldName, newName, newId });
        if (res.success) {
          alert('Voice model updated successfully.');
          document.body.removeChild(formOverlay);
          document.body.removeChild(overlay);
          showVoiceManager(); // Refresh list
          window.populateVoiceModelSelector();
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
  
    async function deleteVoiceModel(name) {
      const confirmDel = confirm(`Are you sure you want to delete the voice model "${name}"?`);
      if (!confirmDel) return;
  
      const res = await window.electronAPI.deleteVoiceModel(name);
      if (res.success) {
        alert('Voice model deleted successfully.');
        document.body.removeChild(overlay);
        showVoiceManager(); // Refresh
        window.populateVoiceModelSelector();
      } else {
        alert(res.message);
      }
    }
  }
  
  // Expose showVoiceManager to the global scope
  window.showVoiceManager = showVoiceManager;
