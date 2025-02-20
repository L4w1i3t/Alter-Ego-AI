// preload.js (Modified: Removed voice model functions)

const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
  // Streaming
  startOllamaStream: (data) => ipcRenderer.send('start-ollama-stream', data),
  detectEmotions: (texts) => ipcRenderer.invoke('detect-emotions', { texts, scoreThreshold: 0 }),

  onOllamaStreamChunk: (callback) => {
    ipcRenderer.on('ollama-stream-chunk', (event, chunkText) => {
      callback(chunkText);
    });
  },
  onOllamaStreamDone: (callback) => {
    ipcRenderer.on('ollama-stream-done', () => {
      callback();
    });
  },
  onOllamaStreamError: (callback) => {
    ipcRenderer.on('ollama-stream-error', (event, errMsg) => {
      callback(errMsg);
    });
  },

  // Simple query (non-stream)
  queryOllama: (data) => ipcRenderer.invoke('query', data),

  // Memory clearing
  clearMemory: () => ipcRenderer.send('clear-memory'),
  onClearMemoryResult: (callback) => {
    ipcRenderer.on('clear-memory-result', (event, data) => callback(event, data));
  },

  // Chat history
  getChatHistory: (personaName) => ipcRenderer.invoke('get-chat-history', personaName),

  // Software details
  getSoftwareDetails: () => ipcRenderer.invoke('get-software-details'),

  // Personas
  getPersonas: () => ipcRenderer.invoke('get-personas'),
  readPersona: (filename) => ipcRenderer.invoke('read-persona', filename),
  addPersona: (data) => ipcRenderer.invoke('add-persona', data),
  updatePersona: (data) => ipcRenderer.invoke('update-persona', data),
  deletePersona: (filename) => ipcRenderer.invoke('delete-persona', filename),

  // API keys
  getApiKeys: () => ipcRenderer.invoke('get-api-keys'),
  updateApiKey: (data) => ipcRenderer.invoke('update-api-key', data),

  onModelPullProgress: (callback) => {
    ipcRenderer.on('model-pull-progress', (event, progress) => callback(progress));
  },
  onModelPullDone: (callback) => {
    ipcRenderer.on('model-pull-done', () => callback());
  },

  streamVoiceResponse: (data) => ipcRenderer.invoke('stream-voice-response', data),
  getVoiceModels: () => ipcRenderer.invoke('getVoiceModels'),
  
  streamVoiceResponse: (data) => ipcRenderer.invoke('stream-voice-response', data),
  deleteTempFile: (filePath) => ipcRenderer.invoke('delete-temp-file', filePath),

  // Warming-up events
  onShowWarmingUp: (callback) => {
    ipcRenderer.on('show-warming-up', (event) => callback(event));
  },
  onHideWarmingUp: (callback) => {
    ipcRenderer.on('hide-warming-up', (event) => callback(event));
  },
  onWarmUpFailure: (callback) => {
    ipcRenderer.on('warm-up-failure', (event) => callback(event));
  },
});
