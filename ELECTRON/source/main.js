/*********************************************************************
 * main.js
 *********************************************************************/

const os = require('os');
const { app, BrowserWindow, ipcMain, dialog } = require('electron');
const path = require('path');
const fs = require('fs');
const { spawn, exec } = require('child_process');
const commandExists = require('command-exists');
require('./ipcHandlers');

// Globals
let wizardWindow = null; // Reference to the setup wizard window
let mainWindow = null;   // Reference to the main application window
let pythonProcess = null;   // Reference to the Python process
let isOllamaUsed = false;   // Flag to indicate if Ollama is used
let ollamaServer = null;    // Reference to the Ollama server process

// Determine Python Executable Early
let pythonExecutable = 'python'; // Default for non-Windows

if (process.platform === 'win32') {
  // Path to embedded Python on Windows
  pythonExecutable = path.join(__dirname, 'Python', 'embedded', 'python.exe');
  if (!fs.existsSync(pythonExecutable)) {
    console.error('Embedded Python executable not found at:', pythonExecutable);
    // Prompt to reinstall or contact support, etc.
  }
}

/*********************************************************************
 * 1) CREATE WIZARD WINDOW
 *********************************************************************/
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

// Helper logs to wizard
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

/*********************************************************************
 * 2) SETUP WIZARD FLOW
 *********************************************************************/
async function runSetupWizard() {
  try {
    if (process.platform === 'win32') {
      // Windows uses embedded Python environment
      wizardLog('Running on Windows. Using embedded Python...');

      // Our checks
      await checkOllama();
      await checkGoEmotionsModel();

      wizardLog('All Windows prerequisites met via embedded environment.');
    } else {
      // Mac/Linux flow: find or install python, ensure pip, etc.
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
    // app.quit(); // optional
  }
}

/*********************************************************************
 * 2A) PYTHON CHECK
 *********************************************************************/
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

/*********************************************************************
 * 2B) PIP CHECK
 *********************************************************************/
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

/*********************************************************************
 * 2C) INSTALL REQUIREMENTS.TXT
 *********************************************************************/
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

/*********************************************************************
 * 2D) CHECK OLLAMA
 *********************************************************************/
/**
 * Because you mentioned “pull won't work unless the server is on,”
 * we start the server first, then spawn the pull. Once pull is done,
 * we explicitly kill the server. That way, there is no orphan.
 */
function checkOllama() {
  return new Promise((resolve, reject) => {
    const ollamaPath = path.join(__dirname, 'api', 'Ollama', 'ollama.exe');
    const ollamaExecutable = process.platform === 'win32' ? ollamaPath : 'ollama';

    if (!fs.existsSync(ollamaPath)) {
      wizardLog('Embeddable Ollama environment NOT found.');
      return reject(new Error('Missing Ollama environment.'));
    }

    // Start the server
    wizardLog('Starting Ollama server to download the base model...');
    ollamaServer = spawn(ollamaExecutable, ['serve']);

    // Verbose logging from the server
    ollamaServer.stdout.on('data', (data) => {
      wizardLog(`[Ollama Server STDOUT] ${data.toString()}`);
    });
    ollamaServer.stderr.on('data', (data) => {
      wizardLog(`[Ollama Server STDERR] ${data.toString()}`);
    });

    ollamaServer.on('close', (code) => {
      wizardLog(`(Server Exited) Ollama server child process exited with code: ${code}`);
    });

    // Now run "ollama pull <model>" to ensure the model is installed
    const modelName = 'artifish/llama3.2-uncensored';
    wizardLog(`Pulling base language model (“${modelName}”). This may take a few minutes...`);

    const pullProcess = spawn(ollamaExecutable, ['pull', modelName]);
    
    // Verbose logging for the pull process
    pullProcess.stdout.on('data', (data) => {
      wizardLog(`[Pull STDOUT] ${data.toString()}`);
    });
    pullProcess.stderr.on('data', (data) => {
      wizardLog(`[Pull STDERR] ${data.toString()}`);
    });

    pullProcess.on('exit', (code) => {
      wizardLog(`[Pull] "ollama pull" process exited with code ${code}.`);

      // Once the pull is done, kill the server
      wizardLog('Stopping the Ollama server now that the pull has finished...');
      stopOllamaServer();

      // We do not consider a non-zero code fatal,
      // so we simply resolve either way:
      resolve();
    });
  });
}

/**
 * Helper to forcibly kill the Ollama server so we do not orphan the pull.
 */
function stopOllamaServer() {
  if (!ollamaServer) {
    wizardLog('No Ollama server process to stop.');
    return;
  }

  const pid = ollamaServer.pid;
  wizardLog(`Attempting to kill Ollama server PID ${pid}...`);

  try {
    if (process.platform === 'win32') {
      spawn('taskkill', ['/PID', String(pid), '/F', '/T']);
    } else {
      ollamaServer.kill('SIGKILL');
    }
  } catch (err) {
    wizardError(`Failed to kill Ollama server: ${err}`);
  }

  ollamaServer = null;
}

/*********************************************************************
 * 2E) CHECK GO EMOTIONS MODEL AND MINILM-L6
 *********************************************************************/
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
      wizardLog('Roberta-base-go_emotions model already cached.');
      resolve();
    } else {
      wizardLog('Roberta-base-go_emotions not found locally. Downloading from Hugging Face...');

      const pythonScriptPath = path.join(__dirname, 'install', 'emotionpipe.py');
      const pythonCmd = process.platform === 'win32' ? pythonExecutable : 'python';

      const downloader = spawn(pythonCmd, [pythonScriptPath]);

      downloader.stdout.on('data', (data) => {
        wizardLog(`[GoEmotions STDOUT] ${data.toString()}`);
      });
      downloader.stderr.on('data', (data) => {
        wizardLog(`[GoEmotions STDERR] ${data.toString()}`);
      });

      downloader.on('close', (code) => {
        if (code === 0) {
          wizardLog('Go Emotions model downloaded successfully.');
          resolve();
        } else {
          reject(new Error('Failed to download Roberta-base-go_emotions model.'));
        }
      });
    }
  });
}

/*********************************************************************
 * 3) IF ALL GOES WELL, CREATE MAIN WINDOW
 *********************************************************************/
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

  // Show model selection once main window is ready
  mainWindow.webContents.once('did-finish-load', () => {
    mainWindow.webContents.send('show-model-selection');
  });

  ipcMain.on('model-selected', (event, modeChoice) => {
    BrowserWindow.getFocusedWindow().webContents.send('show-warming-up');
    isOllamaUsed = (modeChoice === 'ollama');
    startPythonServer(isOllamaUsed ? 'ollama' : 'openai');
  });
}

/*********************************************************************
 * 4) START PYTHON SERVER
 *********************************************************************/
function startPythonServer(modeChoice) {
  let pythonCmd = pythonExecutable; // already determined

  const serverScriptPath = path.join(__dirname, 'api', 'server.py');
  const env = { ...process.env, MODEL_BACKEND: modeChoice };

  // Notify the frontend that we're starting the server
  BrowserWindow.getAllWindows().forEach(win => {
    win.webContents.send('update-warmup-status', {
      message: 'Starting Python server...',
      progress: 10
    });
  });

  pythonProcess = spawn(pythonCmd, [serverScriptPath], {
    cwd: path.join(__dirname, 'api'),
    env
  });

  let serverOutput = '';
  
  pythonProcess.stdout.on('data', (data) => {
    const output = data.toString();
    serverOutput += output;
    console.log(`[Python stdout] ${output}`);
    
    // Parse progress indicators from server output
    if (output.includes('Loading model')) {
      updateWarmupProgress('Loading AI model...', 30);
    } else if (output.includes('Initializing')) {
      updateWarmupProgress('Initializing components...', 50);
    } else if (output.includes('Server starting')) {
      updateWarmupProgress('Server starting...', 70);
    }
  });
  
  pythonProcess.stderr.on('data', (data) => {
    const error = data.toString();
    serverOutput += error;
    console.warn(`[Python stderr] ${error}`);
    
    // Show error in warmup screen if it's critical
    if (error.includes('Error:') || error.includes('Exception:')) {
      updateWarmupProgress(`Error detected: ${error.substring(0, 100)}...`, 0);
    }
  });
  
  pythonProcess.on('close', (code) => {
    console.log(`Python server exited with code ${code}`);
    
    // If server exits unexpectedly during warmup
    if (code !== 0) {
      BrowserWindow.getAllWindows().forEach(win => {
        win.webContents.send('warm-up-failure', {
          message: 'Server exited unexpectedly',
          details: serverOutput
        });
      });
    }
  });

  // Start the server check with better feedback
  checkServerReady();
}

function updateWarmupProgress(message, progressPercent) {
  BrowserWindow.getAllWindows().forEach(win => {
    win.webContents.send('update-warmup-status', {
      message,
      progress: progressPercent
    });
  });
}

async function checkServerReady() {
  const maxAttempts = 60; // Try for about 5 minutes (60 * 5s = 300s or 5 min)
  const delay = 5000; // 5 seconds between attempts
  let attempts = 0;
  let startTime = Date.now();
  
  updateWarmupProgress('Connecting to server...', 20);

  while (attempts < maxAttempts) {
    try {
      updateWarmupProgress(`Checking server readiness (Attempt ${attempts + 1}/${maxAttempts})...`, 
        Math.min(70 + Math.floor((attempts / maxAttempts) * 20), 90));
        
      const response = await fetch('http://127.0.0.1:5000/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: 'warm-up' })
      });
      
      if (response.ok) {
        const timeTaken = ((Date.now() - startTime) / 1000).toFixed(1);
        console.log(`Python server warmed up successfully in ${timeTaken}s.`);
        updateWarmupProgress('Server ready!', 100);
        
        // Small delay so users can see the "ready" message
        setTimeout(() => {
          BrowserWindow.getAllWindows().forEach(win => {
            win.webContents.send('hide-warming-up');
          });
        }, 1500);
        
        return; // Success! Exit the function
      }
    } catch (error) {
      // Only log errors that are not ECONNREFUSED to reduce noise during startup.
      if (!error.cause || error.cause.code !== 'ECONNREFUSED') {
        console.warn('Warm-up attempt error:', error);
      }
      // Otherwise, ignore ECONNREFUSED errors as they are expected until the server is ready.
    }
    
    attempts++;
    
    // If we've reached the maximum attempts, inform the user
    if (attempts >= maxAttempts) {
      BrowserWindow.getAllWindows().forEach(win => {
        win.webContents.send('warm-up-failure', {
          message: 'Server warmup timed out after multiple attempts',
          details: 'The server is taking too long to start. This could be due to hardware limitations or a configuration issue.'
        });
      });
      return;
    }
    
    await new Promise(resolve => setTimeout(resolve, delay));
  }
}

/*********************************************************************
 * 5) APP EVENTS
 *********************************************************************/
app.whenReady().then(() => {
  createWizardWindow();
  runSetupWizard();
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

ipcMain.on('restart-app', () => {
  app.relaunch();
  app.exit();
});

// Also add this to the start of main.js
const maxAppStartupTime = 600000; // 10 minutes
// Add overall app timeout safety mechanism
setTimeout(() => {
  if (BrowserWindow.getAllWindows().length > 0) {
    BrowserWindow.getAllWindows()[0].webContents.send('warm-up-failure', {
      message: 'Application startup timed out',
      details: 'The application took too long to start. This might be due to hardware limitations or unexpected errors.'
    });
  }
}, maxAppStartupTime);