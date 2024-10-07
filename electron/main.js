// electron/main.js
const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const isDev = require('electron-is-dev');

let mainWindow;
let backendProcess;

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1280,
    height: 720,
    webPreferences: {
      preload: path.join(__dirname, 'renderer', 'preload.js'),
      nodeIntegration: true,
      contextIsolation: false,
    },
  });

  const startURL = isDev
    ? 'http://127.0.0.1:8000'
    : `file://${path.join(__dirname, 'renderer', 'index.html')}`;
    mainWindow.loadFile(path.join(__dirname, 'renderer', 'index.html'));
    ;

  mainWindow.on('closed', () => (mainWindow = null));
}

function startBackend() {
  const backendPath = path.join(__dirname, '..', 'api', 'api_server.py');
  backendProcess = spawn('python', [backendPath], {
    cwd: path.join(__dirname, '..'),
    env: process.env,
    stdio: 'inherit',
  });

  backendProcess.on('close', (code) => {
    console.log(`Backend process exited with code ${code}`);
    if (mainWindow) {
      mainWindow.webContents.send('backend-exited', code);
    }
  });

  backendProcess.on('error', (err) => {
    console.error('Failed to start backend:', err);
  });
}

app.whenReady().then(() => {
  startBackend();
  createWindow();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    if (backendProcess) backendProcess.kill();
    app.quit();
  }
});
