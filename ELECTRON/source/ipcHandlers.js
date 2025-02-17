// ipcHandlers.js (Modified: Removed TTS/Voice Model functionality)

const { ipcMain } = require('electron');
const path = require('path');
const fs = require('fs');
const fetch = require('node-fetch');

const {
  // Removed: loadVoiceModels, saveVoiceModels,
  loadKeys,
  saveKeys,
  getPersonaFiles,
  readPersonaFile,
  writePersonaFile,
  deletePersonaFile,
} = require('./utils');

const { queryOllamaStream } = require('./api/localLogic');
const { queryOllamaOnce } = require('./api/localLogic');
const { detectEmotions } = require('./api/goEmotionsLogic');
// Removed: convertTextToSpeech from voiceAgent

// Memory management from memory_manager.js
const {
  loadChatHistory,
  appendChatMessage,
} = require('./assets/js/memory_manager');

// Handler to clear memory
ipcMain.on('clear-memory', async (event) => {
  try {
    const { clearMemory } = require('./assets/js/clear_memory');
    await clearMemory();

    // Optionally call a backend endpoint to clear STM if needed
    const response = await fetch('http://127.0.0.1:5000/clear_stm', { method: 'POST' });
    if (!response.ok) {
      console.warn('Warning: Attempt to clear STM returned non-2xx status:', response.status);
    }
    event.sender.send('clear-memory-result', { success: true, message: 'Memory cleared successfully.' });
  } catch (error) {
    console.error('Error clearing memory:', error);
    event.sender.send('clear-memory-result', { success: false, message: 'Failed to clear memory.' });
  }
});

ipcMain.handle('get-chat-history', async (event, personaName) => {
  try {
    const history = loadChatHistory(personaName);
    return { success: true, history };
  } catch (error) {
    console.error('Error getting chat history for:', personaName, error);
    return { success: false, history: [] };
  }
});

// Handler for retrieving software details
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

// IPC handlers for API keys
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

// IPC handler for emotion detection
ipcMain.handle('detect-emotions', async (event, { texts, scoreThreshold = 0.0 }) => {
  try {
    return await detectEmotions(texts, scoreThreshold);
  } catch (err) {
    console.error('Error in detect-emotions:', err);
    return [];
  }
});

// Comprehensive "query" handler (Voice/TTS functionality removed)
ipcMain.handle('query', async (event, data) => {
  const {
    query,
    persona_name = "ALTER EGO",
    persona_prompt = "You are a program called ALTER EGO.",
  } = data;

  if (!query || typeof query !== 'string') {
    return { error: "Invalid query" };
  }

  // Use the current query as the prompt.
  const final_prompt = `${query}`;

  // Log the user's query.
  appendChatMessage(persona_name, "user", query);

  let answer;
  try {
    answer = await queryOllamaOnce(final_prompt, persona_prompt);
  } catch (err) {
    console.error("Ollama error:", err);
    return { error: err.message };
  }

  // Log the assistant's response.
  appendChatMessage(persona_name, "assistant", answer);

  // Perform emotion detection on both query and response.
  const query_emotions_list = await detectEmotions([query]);
  const response_emotions_list = await detectEmotions([answer]);
  const query_emotions = query_emotions_list[0] || [];
  const response_emotions = response_emotions_list[0] || [];

  return {
    response: answer,
    query_emotions,
    response_emotions,
  };
});

ipcMain.on('start-ollama-stream', (event, { prompt, personaPrompt }) => {
  // Use the exact personaPrompt sent from the front-end.
  queryOllamaStream(
    prompt,
    personaPrompt,
    "",
    (chunkText) => {
      event.sender.send('ollama-stream-chunk', chunkText);
    },
    () => {
      event.sender.send('ollama-stream-done');
    },
    (errMsg) => {
      event.sender.send('ollama-stream-error', errMsg);
    }
  );
});
