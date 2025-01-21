const { ipcMain } = require('electron');
const { clearMemory } = require('./assets/js/clear_memory');
const path = require('path');
const fs = require('fs');
const {
  loadVoiceModels,
  saveVoiceModels,
  loadKeys,
  saveKeys,
  getPersonaFiles,
  readPersonaFile,
  writePersonaFile,
  deletePersonaFile
} = require('./utils');

// Handle memory clearing IPC
ipcMain.on('clear-memory', async (event) => {
  try {
    await clearMemory();
    event.sender.send('clear-memory-result', { success: true, message: 'Memory cleared successfully.' });
  } catch (error) {
    console.error('Error clearing memory:', error);
    event.sender.send('clear-memory-result', { success: false, message: 'Failed to clear memory.' });
  }
});

// Handle IPC for software details
ipcMain.handle('get-software-details', async () => {
  const detailsPath = path.join(__dirname, 'data', 'credits.json');
  try {
    const data = fs.readFileSync(detailsPath, 'utf-8');
    return JSON.parse(data);
  } catch (err) {
    console.error('Error reading software details:', err);
    return null;
  }
});

// IPC handlers for persona management
ipcMain.handle('get-personas', async () => {
  try {
    const personaFiles = getPersonaFiles();
    const personas = personaFiles.map(file => ({ name: file }));
    return { success: true, personas };
  } catch (error) {
    console.error('Error getting personas:', error);
    return { success: false, personas: [] };
  }
});

ipcMain.handle('read-persona', async (event, filename) => {
  try {
    const content = readPersonaFile(filename);
    return { success: true, content };
  } catch (error) {
    console.error('Error reading persona:', error);
    return { success: false, content: '' };
  }
});

ipcMain.handle('add-persona', async (event, { filename, content }) => {
  try {
    if (!filename.endsWith('.chr')) {
      filename += '.chr';
    }
    const personaFiles = getPersonaFiles();
    if (personaFiles.includes(filename)) {
      return { success: false, message: 'Persona file already exists.' };
    }
    writePersonaFile(filename, content);
    return { success: true, message: 'Persona added successfully.' };
  } catch (error) {
    console.error('Error adding persona:', error);
    return { success: false, message: 'Failed to add persona.' };
  }
});

ipcMain.handle('update-persona', async (event, { filename, content }) => {
  try {
    writePersonaFile(filename, content);
    return { success: true, message: 'Persona updated successfully.' };
  } catch (error) {
    console.error('Error updating persona:', error);
    return { success: false, message: 'Failed to update persona.' };
  }
});

ipcMain.handle('delete-persona', async (event, filename) => {
  try {
    deletePersonaFile(filename);
    return { success: true, message: 'Persona deleted successfully.' };
  } catch (error) {
    console.error('Error deleting persona:', error);
    return { success: false, message: 'Failed to delete persona.' };
  }
});

// IPC handlers for voice manager
ipcMain.handle('get-voice-models', async () => {
  try {
    const models = loadVoiceModels();
    return { success: true, models };
  } catch (error) {
    console.error('Error getting voice models:', error);
    return { success: false, models: {} };
  }
});

ipcMain.handle('add-voice-model', async (event, { name, id }) => {
  try {
    const models = loadVoiceModels();
    if (models[name]) {
      return { success: false, message: 'Voice model with this name already exists.' };
    }
    models[name] = id;
    saveVoiceModels(models);
    return { success: true, message: 'Voice model added successfully.' };
  } catch (error) {
    console.error('Error adding voice model:', error);
    return { success: false, message: 'Failed to add voice model.' };
  }
});

ipcMain.handle('update-voice-model', async (event, { oldName, newName, newId }) => {
  try {
    const models = loadVoiceModels();
    if (!models[oldName]) {
      return { success: false, message: 'Original voice model not found.' };
    }
    if (oldName !== newName && models[newName]) {
      return { success: false, message: 'A model with the new name already exists.' };
    }
    // Remove old key if name changed
    if (oldName !== newName) {
      delete models[oldName];
    }
    models[newName] = newId;
    saveVoiceModels(models);
    return { success: true, message: 'Voice model updated successfully.' };
  } catch (error) {
    console.error('Error updating voice model:', error);
    return { success: false, message: 'Failed to update voice model.' };
  }
});

ipcMain.handle('delete-voice-model', async (event, name) => {
  try {
    const models = loadVoiceModels();
    if (!models[name]) {
      return { success: false, message: 'Voice model not found.' };
    }
    delete models[name];
    saveVoiceModels(models);
    return { success: true, message: 'Voice model deleted successfully.' };
  } catch (error) {
    console.error('Error deleting voice model:', error);
    return { success: false, message: 'Failed to delete voice model.' };
  }
});

// IPC handlers for keys
ipcMain.handle('get-api-keys', async () => {
  try {
    const keys = loadKeys();
    return { success: true, keys };
  } catch (error) {
    console.error('Error getting API keys:', error);
    return { success: false, keys: {} };
  }
});

ipcMain.handle('update-api-key', async (event, { keyName, newKeyValue }) => {
  try {
    const keys = loadKeys();
    keys[keyName] = newKeyValue;
    saveKeys(keys);
    return { success: true, message: 'API Key updated successfully.' };
  } catch (error) {
    console.error('Error updating API key:', error);
    return { success: false, message: 'Failed to update API key.' };
  }
});