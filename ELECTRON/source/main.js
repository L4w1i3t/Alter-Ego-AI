const os = require('os');
const { app, BrowserWindow, ipcMain, dialog } = require('electron');
const path = require('path');
const fs = require('fs');
const { spawn, exec } = require('child_process');
const commandExists = require('command-exists');
require('./ipcHandlers');

// Globals
let wizardWindow = null; // Reference to the setup wizard window
let mainWindow = null; // Reference to the main application window
let pythonProcess = null; // Reference to the Python process
let isOllamaUsed = false; // Flag to indicate if Ollama is used
let ollamaServer = null; // Reference to the Ollama server process

// Determine Python Executable Early
let pythonExecutable = 'python'; // Default for non-Windows

if (process.platform === 'win32') {
  // Path to embedded Python on Windows
  pythonExecutable = path.join(__dirname, 'Python', 'embedded', 'python.exe');
  if (!fs.existsSync(pythonExecutable)) {
    // Handle missing embedded Python
    console.error('Embedded Python executable not found at:', pythonExecutable);
    // Prompt to reinstall or contact support on Github
  }
}

// ──────────────────────────────────────────────────────────────────────────────
// 1) CREATE WIZARD WINDOW
// ──────────────────────────────────────────────────────────────────────────────
/**
 * Creates the setup wizard window.
 */
function createWizardWindow() {
  wizardWindow = new BrowserWindow({
    width: 600,
    height: 400,
    resizable: false,
    title: "Setup Wizard",
    icon: path.join(__dirname, 'assets/gui/favicon.ico'),
    autoHideMenuBar: true,
    fullscreenable: false,
    webPreferences: {
      nodeIntegration: true,
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
/**
 * Logs a message to the wizard window and console.
 * @param {string} msg - The message to log.
 */
function wizardLog(msg) {
  if (wizardWindow) {
    wizardWindow.webContents.send('wizard-log', msg);
  }
  console.log('[Wizard Log]', msg);
}

/**
 * Logs an error message to the wizard window and console.
 * @param {string} msg - The error message to log.
 */
function wizardError(msg) {
  if (wizardWindow) {
    wizardWindow.webContents.send('wizard-error', msg);
  }
  console.error('[Wizard Error]', msg);
}

/**
 * Sends a 'wizard-done' message to the wizard window.
 */
function wizardDone() {
  if (wizardWindow) {
    wizardWindow.webContents.send('wizard-done');
  }
}

// ──────────────────────────────────────────────────────────────────────────────
// 2) SETUP WIZARD FLOW
// ──────────────────────────────────────────────────────────────────────────────
/**
 * Runs the setup wizard to check and install necessary dependencies.
 */
async function runSetupWizard() {
  try {
    if (process.platform === 'win32') {
      // Windows uses an embedded Python environment
      wizardLog('Running on Windows. Using embedded Python...');

      // Now do your checks
      await checkOllama();
      await checkGoEmotionsModel();

      wizardLog('All Windows prerequisites met via embedded environment.');
    } else {
      // Mac/Linux flow: find python, ensure pip, install requirements, etc.
      const pythonCmd = await findOrInstallPython();
      wizardLog(`Using Python command: ${pythonCmd}`);

      await ensurePipInstalled(pythonCmd);
      await installRequirements(pythonCmd);

      await checkOllama();
      await checkGoEmotionsModel();

      wizardLog('All requirements have been met on Linux/Mac.');
    }

    wizardDone();
    closeWizardWindow();
  } catch (err) {
    wizardError('Setup error: ' + err.message);
    dialog.showErrorBox('Setup Error', `Unable to complete setup: ${err.message}`);
    // Force quit commented out right now:
    // app.quit();
  }
}

// ──────────────────────────────────────────────────────────────────────────────
// 2A) PYTHON CHECK (No more Windows auto-install)
// ──────────────────────────────────────────────────────────────────────────────
/**
 * Finds or installs Python on the system.
 * @returns {Promise<string>} - The command to use for Python.
 */
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

/**
 * Runs a command in the terminal.
 * @param {string} cmd - The command to run.
 * @param {string[]} args - The arguments for the command.
 * @returns {Promise<void>}
 */
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
/**
 * Ensures that pip is installed for the given Python command.
 * @param {string} pythonCmd - The Python command to use.
 * @returns {Promise<void>}
 */
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
/**
 * Installs the Python dependencies listed in requirements.txt.
 * @param {string} pythonCmd - The Python command to use.
 * @returns {Promise<void>}
 */
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
/**
 * Checks for the Ollama environment and starts the Ollama server.
 * @returns {Promise<void>}
 */
async function checkOllama() {
  return new Promise((resolve, reject) => {
    const ollamaPath = path.join(__dirname, 'api', 'Ollama', 'ollama.exe');
    const ollamaExecutable = process.platform === 'win32' ? ollamaPath : 'ollama';

    if (!fs.existsSync(ollamaPath)) {
      wizardLog('Embeddable Ollama environment NOT found. Ensure ollama.exe is in source/api/Ollama.');
      // Still treat missing ollama as a hard error
      return reject(new Error('Missing Ollama environment.'));
    }

    wizardLog('Found embeddable Ollama environment.');
    wizardLog('Starting Ollama server to download base language model...');

    // 1) Start the Ollama server
    ollamaServer = spawn(ollamaExecutable, ['serve']);

    // Logging from the server
    ollamaServer.stdout.on('data', (data) => {
      wizardLog(`Ollama server: ${data}`);
    });

    ollamaServer.on('close', (code) => {
      wizardLog(`Ollama server exited with code ${code} (Intentional if 1)`);
    });

    // Helper to stop the server safely
    let serverStopped = false;
    function stopServer() {
      if (!serverStopped && ollamaServer) {
        serverStopped = true;
        wizardLog('Stopping Ollama server...');
        if (process.platform === 'win32') {
          spawn('taskkill', ['/PID', String(ollamaServer.pid), '/F', '/T']);
        } else {
          ollamaServer.kill('SIGKILL');
        }
      }
    }

    // If wizard closes, kill server
    if (wizardWindow) {
      wizardWindow.on('closed', () => {
        wizardLog('Wizard closed. Stopping Ollama server...');
        stopServer();
      });
    }

    // 2) Always pull the model
    const modelName = 'artifish/llama3.2-uncensored';
    wizardLog(`Pulling base language model (${modelName}) via Ollama. This may take a few minutes...`);
    const pullProcess = spawn(ollamaExecutable, ['pull', modelName]);

    // 3) On pull complete, stop server and ALWAYS resolve
    pullProcess.on('close', (code) => {
      stopServer();

      if (code === 0) {
        wizardLog(`Base language model pulled successfully: "${modelName}".`);
      } else {
        // Instead of rejecting, we just log the exit code and continue
        wizardLog(`"ollama pull" exited with code ${code}, ignoring and continuing...`);
      }
      // In either case, we resolve
      resolve();
    });
  });
}

// ──────────────────────────────────────────────────────────────────────────────
// 2E) CHECK GO EMOTIONS MODEL (AUTO-DOWNLOAD IF MISSING)
// ──────────────────────────────────────────────────────────────────────────────
/**
 * Checks for the Go Emotions model and downloads it if missing.
 * @returns {Promise<void>}
 */
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
        'Roberta-base-go_emotions not found locally. Downloading from:\n' +
        'https://huggingface.co/SamLowe/roberta-base-go_emotions.'
      );

      const pythonScriptPath = path.join(__dirname, 'install', 'emotionpipe.py');
      const pythonCmd = process.platform === 'win32' ? pythonExecutable : 'python';
      const pythonProcess = spawn(pythonCmd, [pythonScriptPath]);

      pythonProcess.stdout.on('data', (data) => {
        wizardLog(`Download progress: ${data}`);
      });

      pythonProcess.on('close', (code) => {
        if (code === 0) {
          wizardLog('Roberta-base-go_emotions model downloaded successfully.');
          resolve();
        } else {
          reject(new Error('Failed to download Roberta-base-go_emotions model.'));
        }
      });
    }
  });
}

// ──────────────────────────────────────────────────────────────────────────────
// 3) IF ALL GOES WELL, CREATE MAIN WINDOW
// ──────────────────────────────────────────────────────────────────────────────
/**
 * Closes the wizard window and creates the main application window.
 */
function closeWizardWindow() {
  if (wizardWindow) {
    wizardWindow.close();
    wizardWindow = null;
  }
  createMainWindow();
}

/**
 * Creates the main application window.
 */
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

  //“model-selected” logic
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
/**
 * Starts the Python server with the specified mode.
 * @param {string} modeChoice - The mode to use for the server ('ollama' or 'openai').
 */
function startPythonServer(modeChoice) {
  // Use the initialized pythonExecutable
  let pythonCmd = pythonExecutable; // Already set based on OS

  const serverScriptPath = path.join(__dirname, 'api', 'ollama_server.py');
  const env = { ...process.env, MODEL_BACKEND: modeChoice };

  pythonProcess = spawn(pythonCmd, [serverScriptPath], {
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
/**
 * Event handler for when the app is ready.
 */
app.whenReady().then(() => {
  createWizardWindow();
  runSetupWizard();
});

/**
 * Event handler for when the app is activated (e.g., clicked on the dock).
 */
app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createWizardWindow();
    runSetupWizard().catch(err => {
      wizardError(err.message);
    });
  }
});

/**
 * Event handler for when all windows are closed.
 */
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