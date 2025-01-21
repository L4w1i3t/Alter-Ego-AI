const fs = require('fs');
const path = require('path');

const voiceModelsPath = path.join(__dirname, 'persistentdata', 'elevenlabs_models.json');
const keysPath = path.join(__dirname, 'persistentdata', 'keys.json');
const personasPath = path.join(__dirname, 'persistentdata', 'personas');

// Utility functions for voice models
function loadVoiceModels() {
  if (!fs.existsSync(path.dirname(voiceModelsPath))) {
    fs.mkdirSync(path.dirname(voiceModelsPath), { recursive: true });
  }

  if (!fs.existsSync(voiceModelsPath)) {
    const defaultModels = {};
    fs.writeFileSync(voiceModelsPath, JSON.stringify(defaultModels, null, 4), 'utf-8');
    return defaultModels;
  }

  try {
    const fileContent = fs.readFileSync(voiceModelsPath, 'utf-8').trim();
    if (!fileContent) {
      const defaultModels = {};
      fs.writeFileSync(voiceModelsPath, JSON.stringify(defaultModels, null, 4), 'utf-8');
      return defaultModels;
    }
    try {
      const models = JSON.parse(fileContent);
      return models;
    } catch (parseError) {
      console.error('Error parsing voice models JSON:', parseError);
      const backupPath = `${voiceModelsPath}.backup_${Date.now()}`;
      fs.writeFileSync(backupPath, fileContent);

      const defaultModels = {};
      fs.writeFileSync(voiceModelsPath, JSON.stringify(defaultModels, null, 4), 'utf-8');
      console.warn(`Corrupted voice models file backed up to ${backupPath}. Created a new empty file.`);
      return defaultModels;
    }
  } catch (readError) {
    console.error('Error reading voice models file:', readError);
    const defaultModels = {};
    fs.writeFileSync(voiceModelsPath, JSON.stringify(defaultModels, null, 4), 'utf-8');
    return defaultModels;
  }
}

function saveVoiceModels(models) {
  fs.writeFileSync(voiceModelsPath, JSON.stringify(models, null, 4), 'utf-8');
}

// Keys management
function loadKeys() {
  const keysDir = path.dirname(keysPath);
  if (!fs.existsSync(keysDir)) {
    fs.mkdirSync(keysDir, { recursive: true });
  }

  if (!fs.existsSync(keysPath)) {
    const defaultKeys = {
      "OPENAI_API_KEY": "",
      "ELEVENLABS_API_KEY": ""
    };
    fs.writeFileSync(keysPath, JSON.stringify(defaultKeys, null, 4), 'utf-8');
    return defaultKeys;
  }

  const data = fs.readFileSync(keysPath, 'utf-8').trim();
  if (!data) {
    const defaultKeys = {
      "OPENAI_API_KEY": "",
      "ELEVENLABS_API_KEY": ""
    };
    fs.writeFileSync(keysPath, JSON.stringify(defaultKeys, null, 4), 'utf-8');
    return defaultKeys;
  }

  try {
    const keys = JSON.parse(data);
    let changed = false;
    if (typeof keys.OPENAI_API_KEY === 'undefined') {
      keys.OPENAI_API_KEY = "";
      changed = true;
    }
    if (typeof keys.ELEVENLABS_API_KEY === 'undefined') {
      keys.ELEVENLABS_API_KEY = "";
      changed = true;
    }

    if (changed) {
      fs.writeFileSync(keysPath, JSON.stringify(keys, null, 4), 'utf-8');
    }

    return keys;
  } catch (parseError) {
    console.error('Error parsing keys.json:', parseError);
    const backupPath = `${keysPath}.backup_${Date.now()}`;
    fs.writeFileSync(backupPath, data);

    const defaultKeys = {
      "OPENAI_API_KEY": "",
      "ELEVENLABS_API_KEY": ""
    };
    fs.writeFileSync(keysPath, JSON.stringify(defaultKeys, null, 4), 'utf-8');
    console.warn(`Corrupted keys.json backed up to ${backupPath}. A new default keys.json has been created.`);
    return defaultKeys;
  }
}

function saveKeys(keys) {
  fs.writeFileSync(keysPath, JSON.stringify(keys, null, 4), 'utf-8');
}

// Persona management utilities
function getPersonaFiles() {
  if (!fs.existsSync(personasPath)) {
    fs.mkdirSync(personasPath, { recursive: true });
  }
  return fs.readdirSync(personasPath).filter(file => file.endsWith('.chr'));
}

function readPersonaFile(filename) {
  const filePath = path.join(personasPath, filename);
  return fs.readFileSync(filePath, 'utf-8');
}

function writePersonaFile(filename, content) {
  const filePath = path.join(personasPath, filename);
  fs.writeFileSync(filePath, content, 'utf-8');
}

function deletePersonaFile(filename) {
  const filePath = path.join(personasPath, filename);
  fs.unlinkSync(filePath);
}

module.exports = {
  loadVoiceModels,
  saveVoiceModels,
  loadKeys,
  saveKeys,
  getPersonaFiles,
  readPersonaFile,
  writePersonaFile,
  deletePersonaFile
};