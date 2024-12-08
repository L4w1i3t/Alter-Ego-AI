const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
    clearMemory: () => ipcRenderer.send('clear-memory'),
    onClearMemoryResult: (callback) => ipcRenderer.on('clear-memory-result', callback),
    getSoftwareDetails: () => ipcRenderer.invoke('get-software-details')
});
