async function showPersonaManager() {
    // Fetch the list of personas
    const result = await window.electronAPI.getPersonas();
    if (!result.success) {
      alert('Failed to load personas.');
      return;
    }
  
    const personas = result.personas;
  
    // Create overlay
    const overlay = document.createElement('div');
    overlay.classList.add('details-overlay');
  
    // Create box
    const box = document.createElement('div');
    box.classList.add('details-box');
  
    const title = document.createElement('h2');
    title.textContent = 'Manage Personas';
    box.appendChild(title);
  
    const personaList = document.createElement('ul');
    personaList.style.listStyle = 'none';
    personaList.style.padding = '0';
  
    // Add each persona
    personas.forEach(p => {
      const li = document.createElement('li');
      li.style.display = 'flex';
      li.style.alignItems = 'center';
      li.style.justifyContent = 'space-between';
  
      const nameSpan = document.createElement('span');
      nameSpan.textContent = p.name;
      li.appendChild(nameSpan);
  
      // Edit button
      const editBtn = document.createElement('button');
      editBtn.textContent = 'Edit';
      editBtn.addEventListener('click', () => {
        editPersona(p.name);
      });
      li.appendChild(editBtn);
  
      // Delete button
      const delBtn = document.createElement('button');
      delBtn.textContent = 'Delete';
      delBtn.addEventListener('click', () => {
        deletePersona(p.name);
      });
      li.appendChild(delBtn);
  
      personaList.appendChild(li);
    });
  
    box.appendChild(personaList);
  
    // Add Persona button
    const addBtn = document.createElement('button');
    addBtn.textContent = 'Add Persona';
    addBtn.style.display = 'block';
    addBtn.style.margin = '1em auto';
    addBtn.addEventListener('click', () => {
      addPersonaForm();
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
      nameInput.placeholder = 'Persona filename (without .chr)';
      nameInput.style.width = '100%';
      nameInput.style.marginBottom = '1em';
      formBox.appendChild(nameInput);
  
      const textArea = document.createElement('textarea');
      textArea.placeholder = 'Persona content...';
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
          alert('Filename cannot be empty.');
          return;
        }
        const res = await window.electronAPI.addPersona({ filename, content });
        if (res.success) {
          alert('Persona added successfully.');
          document.body.removeChild(formOverlay);
          document.body.removeChild(overlay);
          showPersonaManager(); // Refresh the list
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
  
    async function editPersona(filename) {
      const readRes = await window.electronAPI.readPersona(filename);
      if (!readRes.success) {
        alert('Failed to read persona.');
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
          alert('Persona updated successfully.');
          document.body.removeChild(formOverlay);
          document.body.removeChild(overlay);
          showPersonaManager(); // Refresh list
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
  
    async function deletePersona(filename) {
      const confirmDel = confirm(`Are you sure you want to delete ${filename}?`);
      if (!confirmDel) return;
  
      const res = await window.electronAPI.deletePersona(filename);
      if (res.success) {
        alert('Persona deleted successfully.');
        document.body.removeChild(overlay);
        showPersonaManager(); // Refresh
      } else {
        alert(res.message);
      }
    }
  }
  
  // Expose showPersonaManager to global scope
  window.showPersonaManager = showPersonaManager;
  