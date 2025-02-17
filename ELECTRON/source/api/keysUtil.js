// keysUtil.js
const fs = require('fs');
const path = require('path');
const keysPath = path.join(__dirname, '../persistentdata', 'keys.json');

function loadKeys() {
  if (!fs.existsSync(keysPath)) {
    const defaultKeys = {
      "OPENAI_API_KEY": "",
      "ELEVENLABS_API_KEY": ""
    };
    fs.writeFileSync(keysPath, JSON.stringify(defaultKeys, null, 4), 'utf-8');
    return defaultKeys;
  }
  const data = fs.readFileSync(keysPath, 'utf-8');
  try {
    return JSON.parse(data);
  } catch (err) {
    console.error("Error parsing keys.json:", err);
    return {};
  }
}

module.exports = { loadKeys };
