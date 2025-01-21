const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
    onModelSelection: (callback) => ipcRenderer.on('show-model-selection', callback),
    selectModel: (modeChoice) => ipcRenderer.send('model-selected', modeChoice),
    clearMemory: () => ipcRenderer.send('clear-memory'),
    onClearMemoryResult: (callback) => ipcRenderer.on('clear-memory-result', callback),
    getSoftwareDetails: () => ipcRenderer.invoke('get-software-details'),
    getPersonas: () => ipcRenderer.invoke('get-personas'),
    readPersona: (filename) => ipcRenderer.invoke('read-persona', filename),
    addPersona: (data) => ipcRenderer.invoke('add-persona', data),
    updatePersona: (data) => ipcRenderer.invoke('update-persona', data),
    deletePersona: (filename) => ipcRenderer.invoke('delete-persona', filename),
    getVoiceModels: () => ipcRenderer.invoke('get-voice-models'),
    addVoiceModel: (data) => ipcRenderer.invoke('add-voice-model', data),
    updateVoiceModel: (data) => ipcRenderer.invoke('update-voice-model', data),
    deleteVoiceModel: (name) => ipcRenderer.invoke('delete-voice-model', name),
    getApiKeys: () => ipcRenderer.invoke('get-api-keys'),
    updateApiKey: (data) => ipcRenderer.invoke('update-api-key', data),
    onShowWarmingUp: (callback) => ipcRenderer.on('show-warming-up', callback),
    onHideWarmingUp: (callback) => ipcRenderer.on('hide-warming-up', callback),
});
