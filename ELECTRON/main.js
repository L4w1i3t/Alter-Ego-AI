const { app, BrowserWindow, ipcMain, dialog } = require('electron');
const path = require('path');
const fs = require('fs');

// Import the clearMemory function
const { clearMemory } = require('./assets/js/clear_memory'); // Adjust the path as needed

function createWindow() {
  // Create the browser window.
  const mainWindow = new BrowserWindow({
    width: 1280,
    height: 720,
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

  // Optionally open the DevTools (useful for development).
  // mainWindow.webContents.openDevTools();
}

// Handle IPC message for clearing memory
ipcMain.on('clear-memory', async (event) => {
  const response = await dialog.showMessageBox({
    type: 'warning',
    buttons: ['Yes', 'No'],
    defaultId: 1,
    title: 'Confirm Clear Memory',
    message: 'Are you sure you want to clear all memory? This action cannot be undone.'
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

// Handle IPC message for getting software details
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
