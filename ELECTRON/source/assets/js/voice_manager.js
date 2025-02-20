// voice_manager.js
async function showVoiceManager() {
  const result = await window.electronAPI.getVoiceModels();
  if (!result.success) {
    console.error('Failed to load voice models.');
    return;
  }

  const models = result.models; // e.g. { "ModelName": "SomeVoiceID", ... }

  const overlay = document.createElement('div');
  overlay.classList.add('details-overlay');

  const box = document.createElement('div');
  box.classList.add('details-box');

  const title = document.createElement('h2');
  title.textContent = 'Manage Voice Models';
  box.appendChild(title);

  // Short instructions
  const instructions = document.createElement('p');
  instructions.textContent = 'View, edit, or delete existing voice models, or add new ones.';
  box.appendChild(instructions);

  // Container for the cards
  const cardList = document.createElement('div');
  cardList.classList.add('manager-card-list');

  // Build a card for each voice model
  Object.keys(models).forEach((name) => {
    const model_id = models[name];

    const card = document.createElement('div');
    card.classList.add('manager-card');

    // The name + ID 
    const nameSpan = document.createElement('span');
    nameSpan.classList.add('manager-card-name');
    nameSpan.textContent = `${name}: ${model_id}`;
    card.appendChild(nameSpan);

    // Buttons to the right
    const buttonGroup = document.createElement('div');
    buttonGroup.classList.add('manager-card-buttons');

    // Edit
    const editBtn = document.createElement('button');
    editBtn.classList.add('manager-card-button');
    editBtn.textContent = 'Edit';
    editBtn.addEventListener('click', () => {
      editVoiceModel(name, model_id);
    });
    buttonGroup.appendChild(editBtn);

    // Delete
    const delBtn = document.createElement('button');
    delBtn.classList.add('manager-card-button');
    delBtn.textContent = 'Delete';
    delBtn.addEventListener('click', () => {
      deleteVoiceModel(name);
    });
    buttonGroup.appendChild(delBtn);

    card.appendChild(buttonGroup);
    cardList.appendChild(card);
  });

  box.appendChild(cardList);

  // “Add Voice Model” button
  const addBtn = document.createElement('button');
  addBtn.textContent = 'Add Voice Model';
  addBtn.style.display = 'block';
  addBtn.style.margin = '1em auto';
  addBtn.addEventListener('click', () => {
    addVoiceModelForm();
  });
  box.appendChild(addBtn);

  // Close
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
      const newName = nameInput.value.trim();
      const newId = idInput.value.trim();
      if (!newName || !newId) {
        console.log('Name or ID is empty; not saving.');
        return;
      }
      const res = await window.electronAPI.addVoiceModel({ name: newName, id: newId });
      if (res.success) {
        console.log('Voice model added successfully.');
        document.body.removeChild(formOverlay);
        document.body.removeChild(overlay);
        showVoiceManager(); // refresh
        window.populateVoiceModelSelector(); // refresh voice dropdown
      } else {
        console.error(res.message);
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
        console.log('Name or ID is empty; not updating.');
        return;
      }
      const res = await window.electronAPI.updateVoiceModel({ oldName, newName, newId });
      if (res.success) {
        console.log('Voice model updated successfully.');
        document.body.removeChild(formOverlay);
        document.body.removeChild(overlay);
        showVoiceManager();  // refresh
        window.populateVoiceModelSelector(); // refresh voice dropdown
      } else {
        console.error(res.message);
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
    const res = await window.electronAPI.deleteVoiceModel(name);
    if (res.success) {
      console.log('Voice model deleted successfully.');
      document.body.removeChild(overlay);
      showVoiceManager();
      window.populateVoiceModelSelector();
    } else {
      console.error(res.message);
    }
  }
}

// Expose to global scope
window.showVoiceManager = showVoiceManager;
