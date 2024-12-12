const { app, BrowserWindow, ipcMain, dialog } = require('electron');
const path = require('path');
const fs = require('fs');

// Import the clearMemory function
const { clearMemory } = require('./assets/js/clear_memory');
const voiceModelsPath = path.join(__dirname, 'persistentdata', 'elevenlabs_models.json');
const keysPath = path.join(__dirname, 'persistentdata', 'keys.json');
const personasPath = path.join(__dirname, 'persistentdata', 'personas');

function createWindow() {
  // Create the browser window.
  const mainWindow = new BrowserWindow({
    width: 1280,
    height: 720,
    minWidth: 1280,
    minHeight: 720,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'), // Use preload
      nodeIntegration: false, // Disable Node integration for security
      contextIsolation: true, // Enable context isolation for security
    },
    autoHideMenuBar: true,
    icon: path.join(__dirname, 'assets/gui/favicon.ico')
  });

  // Load the index.html of the app.
  mainWindow.loadFile('index.html');
  // Completely remove the menu bar.
  mainWindow.setMenuBarVisibility(false);

  // Open dev mode if needed.
  // mainWindow.webContents.openDevTools();
}

// Handle memory clearing IPC
ipcMain.on('clear-memory', async (event) => {
  const response = await dialog.showMessageBox({
    type: 'warning',
    buttons: ['Yes', 'No'],
    defaultId: 1,
    title: 'Double Confirm',
    message: 'ARE YOU ABSOLUTELY SURE? YOU CANNOT GET THESE MEMORIES BACK.'
  });

  if (response.response === 0) { // 'Yes' button
    try {
      await clearMemory();
      event.sender.send('clear-memory-result', { success: true, message: 'Memory cleared successfully.' });
    } catch (error) {
      console.error('Error clearing memory:', error);
      event.sender.send('clear-memory-result', { success: false, message: 'Failed to clear memory.' });
    }
  } else {
    event.sender.send('clear-memory-result', { success: false, message: 'Memory clearing canceled.' });
  }
});

// Handle IPC for getting software details
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

// Persona management utilities
function getPersonaFiles() {
  if (!fs.existsSync(personasPath)) {
    fs.mkdirSync(personasPath, { recursive: true });
  }
  return fs.readdirSync(personasPath).filter(file => file.endsWith('.chr'));
}

function readPersonaFile(filename) {
  const filePath = path.join(personasPath, filename);
  return fs.readFileSync(filePath, 'utf-8');
}

function writePersonaFile(filename, content) {
  const filePath = path.join(personasPath, filename);
  fs.writeFileSync(filePath, content, 'utf-8');
}

function deletePersonaFile(filename) {
  const filePath = path.join(personasPath, filename);
  fs.unlinkSync(filePath);
}

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

// Utility functions for voice models
function loadVoiceModels() {
  // Ensure the directory exists
  if (!fs.existsSync(path.dirname(voiceModelsPath))) {
    fs.mkdirSync(path.dirname(voiceModelsPath), { recursive: true });
  }

  // Check if file exists
  if (!fs.existsSync(voiceModelsPath)) {
    // File doesn't exist, create it with an empty object
    const defaultModels = {};
    fs.writeFileSync(voiceModelsPath, JSON.stringify(defaultModels, null, 4), 'utf-8');
    return defaultModels;
  }

  try {
    // Read the file content
    const fileContent = fs.readFileSync(voiceModelsPath, 'utf-8').trim();

    // Check if file is empty or just contains whitespace
    if (!fileContent) {
      // Empty file, initialize with an empty object
      const defaultModels = {};
      fs.writeFileSync(voiceModelsPath, JSON.stringify(defaultModels, null, 4), 'utf-8');
      return defaultModels;
    }

    // Try to parse the JSON
    try {
      const models = JSON.parse(fileContent);
      return models;
    } catch (parseError) {
      console.error('Error parsing voice models JSON:', parseError);
      
      // If parsing fails, create a backup of the corrupted file
      const backupPath = `${voiceModelsPath}.backup_${Date.now()}`;
      fs.writeFileSync(backupPath, fileContent);
      
      // Create a new empty object
      const defaultModels = {};
      fs.writeFileSync(voiceModelsPath, JSON.stringify(defaultModels, null, 4), 'utf-8');
      
      console.warn(`Corrupted voice models file backed up to ${backupPath}. Created a new empty file.`);
      return defaultModels;
    }
  } catch (readError) {
    console.error('Error reading voice models file:', readError);
    
    // Fallback to an empty object
    const defaultModels = {};
    fs.writeFileSync(voiceModelsPath, JSON.stringify(defaultModels, null, 4), 'utf-8');
    return defaultModels;
  }
}

function saveVoiceModels(models) {
  fs.writeFileSync(voiceModelsPath, JSON.stringify(models, null, 4), 'utf-8');
}

// IPC handlers for voice manager
ipcMain.handle('get-voice-models', async () => {
  try {
    const models = loadVoiceModels();
    // models is an object: { "Name": "ID", ... }
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

function loadKeys() {
  if (!fs.existsSync(keysPath)) {
    return {};
  }
  const data = fs.readFileSync(keysPath, 'utf-8');
  return JSON.parse(data);
}

function saveKeys(keys) {
  fs.writeFileSync(keysPath, JSON.stringify(keys, null, 4), 'utf-8');
}

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

// This method will be called when Electron has finished initialization.
app.whenReady().then(() => {
  createWindow();

  app.on('activate', function () {
    // On macOS, re-create a window in the app when the dock icon is clicked
    // and there are no other windows open.
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

// Quit when all windows are closed, except on macOS.
app.on('window-all-closed', function () {
  if (process.platform !== 'darwin') app.quit();
});
