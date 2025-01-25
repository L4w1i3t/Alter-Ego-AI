async function showPersonaManager() {
  const result = await window.electronAPI.getPersonas();
  if (!result.success) {
    console.error('Failed to load personas.');
    return;
  }

  const personas = result.personas; // e.g. [{ name: "Historian.chr" }, ... ]

  // Dark overlay
  const overlay = document.createElement('div');
  overlay.classList.add('details-overlay');

  // Main container box
  const box = document.createElement('div');
  box.classList.add('details-box');

  const title = document.createElement('h2');
  title.textContent = 'Manage Personas';
  box.appendChild(title);

  // A short description or instructions
  const instructions = document.createElement('p');
  instructions.textContent = 'View, edit, or delete existing personas, or add new ones.';
  box.appendChild(instructions);

  // Container that will hold the “cards”
  const cardList = document.createElement('div');
  cardList.classList.add('manager-card-list');

  // Create a card for each persona
  personas.forEach((p) => {
    const card = document.createElement('div');
    card.classList.add('manager-card');

    // The name (filename) of this persona
    const nameSpan = document.createElement('span');
    nameSpan.classList.add('manager-card-name');
    nameSpan.textContent = p.name; 
    card.appendChild(nameSpan);

    // Button group to the right
    const buttonGroup = document.createElement('div');
    buttonGroup.classList.add('manager-card-buttons');

    // Edit button
    const editBtn = document.createElement('button');
    editBtn.classList.add('manager-card-button');
    editBtn.textContent = 'Edit';
    editBtn.addEventListener('click', () => {
      editPersona(p.name);
    });
    buttonGroup.appendChild(editBtn);

    // Delete button
    const delBtn = document.createElement('button');
    delBtn.classList.add('manager-card-button');
    delBtn.textContent = 'Delete';
    delBtn.addEventListener('click', () => {
      deletePersona(p.name);
    });
    buttonGroup.appendChild(delBtn);

    card.appendChild(buttonGroup);
    cardList.appendChild(card);
  });

  box.appendChild(cardList);

  // Button to add a persona
  const addBtn = document.createElement('button');
  addBtn.textContent = 'Add Persona';
  addBtn.style.display = 'block';
  addBtn.style.margin = '1em auto';
  addBtn.addEventListener('click', () => {
    addPersonaForm();
  });
  box.appendChild(addBtn);

  // Close panel
  const closeBtn = document.createElement('button');
  closeBtn.textContent = 'Close';
  closeBtn.classList.add('close-details-btn');
  closeBtn.addEventListener('click', () => {
    document.body.removeChild(overlay);
  });
  box.appendChild(closeBtn);

  overlay.appendChild(box);
  document.body.appendChild(overlay);

  async function addPersonaForm() {
    const formOverlay = document.createElement('div');
    formOverlay.classList.add('details-overlay');

    const formBox = document.createElement('div');
    formBox.classList.add('details-box');

    const formTitle = document.createElement('h2');
    formTitle.textContent = 'Add New Persona';
    formBox.appendChild(formTitle);

    const nameInput = document.createElement('input');
    nameInput.type = 'text';
    nameInput.placeholder = 'Name (without .chr)';
    nameInput.style.width = '100%';
    nameInput.style.marginBottom = '1em';
    formBox.appendChild(nameInput);

    const textArea = document.createElement('textarea');
    textArea.placeholder = 'Content';
    textArea.style.width = '100%';
    textArea.style.height = '200px';
    formBox.appendChild(textArea);

    const saveBtn = document.createElement('button');
    saveBtn.textContent = 'Save';
    saveBtn.style.marginTop = '1em';
    saveBtn.addEventListener('click', async () => {
      const filename = nameInput.value.trim();
      const content = textArea.value;
      if (!filename) {
        console.log('Filename is empty; not saving persona.');
        return;
      }
      const res = await window.electronAPI.addPersona({ filename, content });
      if (res.success) {
        console.log('Persona added successfully.');
        document.body.removeChild(formOverlay);
        document.body.removeChild(overlay);
        showPersonaManager(); // refresh
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

  async function editPersona(filename) {
    const readRes = await window.electronAPI.readPersona(filename);
    if (!readRes.success) {
      console.error('Failed to read persona.');
      return;
    }

    const formOverlay = document.createElement('div');
    formOverlay.classList.add('details-overlay');

    const formBox = document.createElement('div');
    formBox.classList.add('details-box');

    const formTitle = document.createElement('h2');
    formTitle.textContent = `Edit ${filename}`;
    formBox.appendChild(formTitle);

    const textArea = document.createElement('textarea');
    textArea.style.width = '100%';
    textArea.style.height = '200px';
    textArea.value = readRes.content;
    formBox.appendChild(textArea);

    const saveBtn = document.createElement('button');
    saveBtn.textContent = 'Save Changes';
    saveBtn.style.marginTop = '1em';
    saveBtn.addEventListener('click', async () => {
      const content = textArea.value;
      const res = await window.electronAPI.updatePersona({ filename, content });
      if (res.success) {
        console.log('Persona updated successfully.');
        document.body.removeChild(formOverlay);
        document.body.removeChild(overlay);
        showPersonaManager(); // refresh
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

  async function deletePersona(filename) {
    // No confirm() call, just proceed
    const res = await window.electronAPI.deletePersona(filename);
    if (res.success) {
      console.log('Persona deleted successfully.');
      document.body.removeChild(overlay);
      showPersonaManager(); // Refresh
    } else {
      console.error(res.message);
    }
  }
}
// Expose to global scope
window.showPersonaManager = showPersonaManager;