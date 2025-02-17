/*********************************************************************
 * main.js
 *********************************************************************/
const { app, BrowserWindow } = require('electron');
const path = require('path');
const { spawn, execSync } = require('child_process');
require('./ipcHandlers.js');

let mainWindow = null;
let ollamaServerProcess = null;

function createMainWindow() {
  mainWindow = new BrowserWindow({
    width: 1280,
    height: 720,
    minWidth: 1280,
    minHeight: 720,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      nodeIntegration: false,
      contextIsolation: true,
      devTools: true,
    },
    autoHideMenuBar: true,
    icon: path.join(__dirname, 'assets/gui/favicon.ico')
  });

  // Optionally open Developer Tools
  //mainWindow.webContents.openDevTools();

  mainWindow.loadFile('index.html');
  mainWindow.setMenuBarVisibility(false);
}

function startOllamaServer() {
  const ollamaExePath = path.join(__dirname, 'api', 'Ollama', 'ollama.exe');
  ollamaServerProcess = spawn(ollamaExePath, ['serve']);

  ollamaServerProcess.stdout.on('data', (data) => {
    console.log(`Ollama server: ${data}`);
  });
  ollamaServerProcess.stderr.on('data', (data) => {
    console.error(`Ollama server error: ${data}`);
  });
  ollamaServerProcess.on('close', (code) => {
    console.log(`Ollama server exited with code ${code}`);
  });
}

function pullModel() {
  const ollamaExePath = path.join(__dirname, 'api', 'Ollama', 'ollama.exe');
  // Spawn the pull process for the model
  const pullProcess = spawn(ollamaExePath, ['pull', 'artifish/llama3.2-uncensored']);

  pullProcess.stdout.on('data', (chunk) => {
    parseProgressChunk(chunk);
  });
  pullProcess.stderr.on('data', (chunk) => {
    parseProgressChunk(chunk);
  });  

  pullProcess.on('close', (code) => {
    console.log(`Model pull process exited with code ${code}`);
    if (mainWindow) {
      mainWindow.webContents.send('model-pull-done');
    }
  });
}

function parseProgressChunk(chunk) {
  const text = chunk.toString('utf8');
  // Replace carriage returns with newlines so we can split easily
  const lines = text.replace(/\r/g, '\n').split('\n');
  lines.forEach(line => {
    console.log('Model Pull:', line); // For debugging
    const progress = extractProgress(line);
    if (progress !== null && mainWindow) {
      mainWindow.webContents.send('model-pull-progress', progress);
    }
  });
}

function extractProgress(line) {
  const match = line.match(/(\d+)%/);
  return match ? parseInt(match[1], 10) : null;
}

function killOllamaServer() {
  if (ollamaServerProcess && !ollamaServerProcess.killed) {
    try {
      execSync(`taskkill /pid ${ollamaServerProcess.pid} /T /F`);
      console.log('Ollama server process tree killed.');
    } catch (error) {
      console.error('Failed to kill Ollama server process:', error);
    }
  }
}

app.whenReady().then(() => {
  startOllamaServer();
  createMainWindow();
  // Start pulling the model once the main window exists (for IPC support)
  pullModel();
});

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createMainWindow();
  }
});

app.on('window-all-closed', () => {
  killOllamaServer();
  app.quit();
});

app.on('will-quit', () => {
  try {
    execSync('taskkill /IM ollama.exe /F');
    execSync('taskkill /IM ollama_llama_server.exe /F');
    console.log('Ollama processes killed.');
  } catch (error) {
    console.error('Error killing ollama processes:', error);
  }
});
