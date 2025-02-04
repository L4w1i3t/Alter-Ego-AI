const fs = require('fs');
const path = require('path');

// We’ll store each persona’s chat history in:
//  persistentdata/memory_databases/<PERSONA_NAME>/chat_history.json
function getChatHistoryPath(personaName) {
  return path.join(
    __dirname,
    '../../persistentdata/memory_databases',
    personaName,
    'chat_history.json'
  );
}

/**
 * Load chat history for a given persona.
 * Returns an array of {timestamp, role, content}.
 */
function loadChatHistory(personaName) {
  try {
    const folderPath = path.join(__dirname, '../../persistentdata/memory_databases', personaName);
    if (!fs.existsSync(folderPath)) {
      fs.mkdirSync(folderPath, { recursive: true });
    }

    const filePath = getChatHistoryPath(personaName);
    if (!fs.existsSync(filePath)) {
      // If no file yet, return empty
      return [];
    }

    const raw = fs.readFileSync(filePath, 'utf-8');
    if (!raw.trim()) {
      return [];
    }
    return JSON.parse(raw);
  } catch (err) {
    console.error(`[loadChatHistory] Error for persona "${personaName}":`, err);
    return [];
  }
}

/**
 * Save chat history array for a given persona.
 */
function saveChatHistory(personaName, historyArray) {
  try {
    const filePath = getChatHistoryPath(personaName);
    fs.writeFileSync(filePath, JSON.stringify(historyArray, null, 2), 'utf-8');
  } catch (err) {
    console.error(`[saveChatHistory] Error for persona "${personaName}":`, err);
  }
}

/**
 * Append a single new message (with role/user/assistant + content + timestamp)
 * to the persona’s chat_history.json.
 */
function appendChatMessage(personaName, role, content) {
  const history = loadChatHistory(personaName);
  const newEntry = {
    timestamp: new Date().toISOString(),
    role,
    content,
  };
  history.push(newEntry);
  saveChatHistory(personaName, history);
}

// Expose these functions for use by ipcHandlers or the Python server flow:
module.exports = {
  loadChatHistory,
  saveChatHistory,
  appendChatMessage,
};
