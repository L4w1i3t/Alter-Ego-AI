// main.js
const os = require('os');
const { app, BrowserWindow, ipcMain, dialog } = require('electron');
const path = require('path');
const fs = require('fs');
const { spawn, exec } = require('child_process'); // removed execFile
const commandExists = require('command-exists');
require('./ipcHandlers');

// Globals
let wizardWindow = null;
let mainWindow = null;
let pythonProcess = null;
let isOllamaUsed = false;

// ──────────────────────────────────────────────────────────────────────────────
// 1) CREATE WIZARD WINDOW
// ──────────────────────────────────────────────────────────────────────────────
function createWizardWindow() {
  wizardWindow = new BrowserWindow({
    width: 600,
    height: 400,
    resizable: false,
    title: "Setup Wizard",
    icon: path.join(__dirname, 'assets/gui/favicon.ico'), // same as main window
    autoHideMenuBar: true,
    fullscreenable: false,
    webPreferences: {
      nodeIntegration: true, // or use contextIsolation + a preload
      contextIsolation: false
    }
  });

  wizardWindow.setMenuBarVisibility(false);
  wizardWindow.loadFile('wizard.html');
  
  wizardWindow.on('closed', () => {
    wizardWindow = null;
  });
}

// Helpers to send logs/errors to wizard
function wizardLog(msg) {
  if (wizardWindow) {
    wizardWindow.webContents.send('wizard-log', msg);
  }
  console.log('[Wizard Log]', msg);
}
function wizardError(msg) {
  if (wizardWindow) {
    wizardWindow.webContents.send('wizard-error', msg);
  }
  console.error('[Wizard Error]', msg);
}
function wizardDone() {
  if (wizardWindow) {
    wizardWindow.webContents.send('wizard-done');
  }
}

// ──────────────────────────────────────────────────────────────────────────────
// 2) SETUP WIZARD FLOW
// ──────────────────────────────────────────────────────────────────────────────
async function runSetupWizard() {
  // If Windows, skip installing or checking Python/pip entirely
  if (process.platform === 'win32') {
    wizardLog('Running on Windows. Skipping Python & pip checks; using embedded Python.');

    // Still require Ollama + GoEmotions model if needed
    await checkOllama();
    await checkGoEmotionsModel();

    wizardLog('All Windows prerequisites met via embedded environment & manual steps.');
    wizardDone();
    closeWizardWindow();

  } else {
    // Non-Windows: do the normal checks
    const pythonCmd = await findOrInstallPython();
    wizardLog(`Using Python command: ${pythonCmd}`);

    await ensurePipInstalled(pythonCmd);
    await installRequirements(pythonCmd);

    await checkOllama();
    await checkGoEmotionsModel();

    wizardLog('All requirements have been met!');
    wizardDone();
    closeWizardWindow();
  }
}

// ──────────────────────────────────────────────────────────────────────────────
// 2A) PYTHON CHECK (No more Windows auto-install)
// ──────────────────────────────────────────────────────────────────────────────
async function findOrInstallPython() {
  try {
    await commandExists('python');
    wizardLog('Found "python" in PATH.');
    return 'python';
  } catch {
    try {
      await commandExists('python3');
      wizardLog('Found "python3" in PATH.');
      return 'python3';
    } catch {
      wizardLog('Python not found. Attempting to auto-install...');
      const platform = process.platform;

      if (platform === 'darwin') {
        await runCommand('brew', ['install', 'python']);
      } else if (platform === 'linux') {
        await runCommand('sudo', ['apt-get', 'update']);
        await runCommand('sudo', ['apt-get', 'install', '-y', 'python3']);
      } else {
        throw new Error('Unsupported OS for auto-install. Please install Python manually.');
      }
      // Re-check
      try {
        await commandExists('python');
        return 'python';
      } catch {
        await commandExists('python3');
        return 'python3';
      }
    }
  }
}

// Simplified runCommand (still needed for mac/linux install)
function runCommand(cmd, args) {
  return new Promise((resolve, reject) => {
    wizardLog(`Running: ${cmd} ${args.join(' ')}`);
    const child = spawn(cmd, args, { stdio: 'inherit' });
    child.on('error', reject);
    child.on('close', code => {
      if (code === 0) resolve();
      else reject(new Error(`"${cmd} ${args.join(' ')}" exited with code ${code}`));
    });
  });
}

// ──────────────────────────────────────────────────────────────────────────────
// 2B) PIP CHECK
// ──────────────────────────────────────────────────────────────────────────────
function ensurePipInstalled(pythonCmd) {
  return new Promise((resolve, reject) => {
    exec(`${pythonCmd} -m pip --version`, (error, stdout) => {
      if (error) {
        wizardLog('pip not found. Trying "ensurepip --upgrade"...');
        exec(`${pythonCmd} -m ensurepip --upgrade`, (err2) => {
          if (err2) {
            return reject(new Error(`Failed to install pip: ${err2.message}`));
          }
          wizardLog('pip installed successfully.');
          resolve();
        });
      } else {
        wizardLog(`Found pip: ${stdout.trim()}`);
        resolve();
      }
    });
  });
}

// ──────────────────────────────────────────────────────────────────────────────
// 2C) INSTALL REQUIREMENTS.TXT
// ──────────────────────────────────────────────────────────────────────────────
function installRequirements(pythonCmd) {
  return new Promise((resolve, reject) => {
    const reqPath = path.join(__dirname, 'api', 'requirements.txt');
    if (!fs.existsSync(reqPath)) {
      wizardLog(`No requirements.txt found at ${reqPath}, skipping...`);
      return resolve();
    }
    wizardLog(`Installing dependencies from ${reqPath}...`);
    exec(`${pythonCmd} -m pip install --upgrade -r "${reqPath}"`, (error, stdout, stderr) => {
      if (error) {
        return reject(new Error(`pip install failed: ${stderr || error.message}`));
      }
      wizardLog('Python dependencies installed:\n' + stdout);
      resolve();
    });
  });
}

// ──────────────────────────────────────────────────────────────────────────────
// 2D) CHECK OLLAMA
// ──────────────────────────────────────────────────────────────────────────────
async function checkOllama() {
  return new Promise((resolve, reject) => {
    const ollamaPath = path.join(__dirname, 'api', 'Ollama', 'ollama.exe');
    if (fs.existsSync(ollamaPath)) {
      wizardLog('Embeddable Ollama environment is found.');
      resolve();
    } else {
      wizardLog('Embeddable Ollama environment is NOT found. Ensure ollama.exe is in the source/Ollama directory.');
      reject(new Error('Embeddable Ollama environment is missing.'));
    }
  });
}

// ──────────────────────────────────────────────────────────────────────────────
// 2E) CHECK GO EMOTIONS MODEL (MUST BE DOWNLOADED)
// ──────────────────────────────────────────────────────────────────────────────
function checkGoEmotionsModel() {
  return new Promise((resolve, reject) => {
    const home = os.homedir();
    const modelPath = path.join(
      home,
      '.cache',
      'huggingface',
      'hub',
      'models--SamLowe--roberta-base-go_emotions'
    );
    if (fs.existsSync(modelPath)) {
      wizardLog('Roberta-base-go_emotions is already downloaded in huggingface cache.');
      resolve();
    } else {
      wizardLog(
        'Roberta-base-go_emotions not found locally. Download from:\n' +
        'https://huggingface.co/SamLowe/roberta-base-go_emotions.'
      );
      //reject(new Error('Go Emotions model is missing.'));
    }
  });
}

// ──────────────────────────────────────────────────────────────────────────────
// 3) IF ALL GOES WELL, CREATE MAIN WINDOW
// ──────────────────────────────────────────────────────────────────────────────
function closeWizardWindow() {
  if (wizardWindow) {
    wizardWindow.close();
    wizardWindow = null;
  }
  createMainWindow();
}

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
    },
    autoHideMenuBar: true,
    icon: path.join(__dirname, 'assets/gui/favicon.ico')
  });

  mainWindow.setMenuBarVisibility(false);
  mainWindow.loadFile('index.html');

  // Original “model-selected” logic
  mainWindow.webContents.once('did-finish-load', () => {
    mainWindow.webContents.send('show-model-selection');
  });

  ipcMain.on('model-selected', (event, modeChoice) => {
    BrowserWindow.getFocusedWindow().webContents.send('show-warming-up');
    isOllamaUsed = (modeChoice === 'ollama');
    startPythonServer(isOllamaUsed ? 'ollama' : 'openai');
  });
}

// ──────────────────────────────────────────────────────────────────────────────
// 4) START PYTHON SERVER
// ──────────────────────────────────────────────────────────────────────────────
function startPythonServer(modeChoice) {
  // If Windows, use embedded python.exe; else system python
  let pythonExecutable;
  if (process.platform === 'win32') {
    pythonExecutable = path.join(__dirname, 'Python', 'embedded', 'python.exe');
  } else {
    pythonExecutable = 'python';
  }

  const serverScriptPath = path.join(__dirname, 'api', 'ollama_server.py');
  const env = { ...process.env, MODEL_BACKEND: modeChoice };

  pythonProcess = spawn(pythonExecutable, [serverScriptPath], {
    cwd: path.join(__dirname, 'api'),
    env
  });

  pythonProcess.stdout.on('data', (data) => {
    console.log(`[Python stdout] ${data}`);
  });

  pythonProcess.stderr.on('data', (data) => {
    console.warn(`[Python stderr] ${data}`);
  });

  pythonProcess.on('close', (code) => {
    console.log(`Python server exited with code ${code}`);
  });

  // Warm up logic
  const checkServerReady = async (retries = 5, delay = 2000) => {
    for (let i = 0; i < retries; i++) {
      try {
        const response = await fetch('http://127.0.0.1:5000/query', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ query: 'warm-up' })
        });
        if (response.ok) {
          console.log('Python server warmed up successfully.');
          const allWindows = BrowserWindow.getAllWindows();
          if (allWindows.length > 0) {
            allWindows[0].webContents.send('hide-warming-up');
          }
          return;
        }
      } catch (error) {
        console.warn(`Attempt ${i+1} - Error warming up:`, error);
      }
      await new Promise(resolve => setTimeout(resolve, delay));
    }
    console.warn('Failed to warm up server after multiple attempts.');
  };

  setTimeout(() => {
    checkServerReady();
  }, 5000);
}

// ──────────────────────────────────────────────────────────────────────────────
// 5) APP EVENTS
// ──────────────────────────────────────────────────────────────────────────────
app.whenReady().then(() => {
  createWizardWindow();
  runSetupWizard()
    .catch(err => {
      wizardError('Setup error: ' + err.message);
      dialog.showErrorBox('Setup Error', `Unable to complete setup: ${err.message}`);
      // If desired, you can keep wizard open or close+quit:
      // app.quit();
    });
});

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createWizardWindow();
    runSetupWizard().catch(err => {
      wizardError(err.message);
    });
  }
});

app.on('window-all-closed', async () => {
  try {
    // Attempt graceful shutdown
    const response = await fetch('http://127.0.0.1:5000/stop', { method: 'POST' });
    if (!response.ok) {
      console.warn('Could not stop Python server gracefully.');
    }
  } catch (error) {
    console.warn('Could not call /stop:', error);
  }

  // Forcibly kill python if needed
  if (pythonProcess) {
    await new Promise(resolve => setTimeout(resolve, 1000));
    if (pythonProcess.exitCode === null) {
      console.log('Python still alive - forcibly killing.');
      if (process.platform === 'win32') {
        spawn('taskkill', ['/PID', String(pythonProcess.pid), '/F', '/T']);
      } else {
        pythonProcess.kill('SIGKILL');
      }
    }
  }
  app.quit();
});
