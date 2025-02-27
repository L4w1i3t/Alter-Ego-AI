const sqlite3 = require('sqlite3').verbose();
const fs = require('fs');
const path = require('path');

const memoryDatabasesPath = path.join(__dirname, '../../persistentdata/memory_databases');

function clearMemory() {
  return new Promise((resolve, reject) => {
    fs.readdir(memoryDatabasesPath, (err, folders) => {
      if (err) {
        console.error('Error reading memory_databases directory:', err);
        return reject(err);
      }

      const operations = [];

      folders.forEach((folder) => {
        const folderPath = path.join(memoryDatabasesPath, folder);
        if (fs.lstatSync(folderPath).isDirectory()) {
          const dbPath = path.join(folderPath, 'memory.db');
          const chatHistoryPath = path.join(folderPath, 'chat_history.json');

          // Clear SQLite database
          const dbOp = new Promise((res, rej) => {
            if (fs.existsSync(dbPath)) {
              const db = new sqlite3.Database(dbPath, sqlite3.OPEN_READWRITE, (err) => {
                if (err) {
                  console.error(`Error opening DB at ${dbPath}:`, err);
                  return rej(err);
                }
              });
              db.run("DELETE FROM memory_entries", function(err) {
                if (err) {
                  console.error(`Error clearing memory_entries in ${dbPath}:`, err);
                  db.close();
                  return rej(err);
                }
                // Optional: run VACUUM to optimize the DB file
                db.run("VACUUM", function(err) {
                  if (err) {
                    console.error(`Error vacuuming DB at ${dbPath}:`, err);
                  }
                  db.close();
                  res();
                });
              });
            } else {
              res();
            }
          });
          operations.push(dbOp);

          // Clear chat_history.json file
          const chatOp = new Promise((res, rej) => {
            fs.writeFile(chatHistoryPath, '[]', 'utf8', (err) => {
              if (err) {
                console.error(`Error clearing chat history at ${chatHistoryPath}:`, err);
                return rej(err);
              }
              res();
            });
          });
          operations.push(chatOp);
        }
      });

      Promise.all(operations)
        .then(() => {
          console.log('Cleared all memory (database and chat history) without deleting folders.');
          resolve();
        })
        .catch(reject);
    });
  });
}

module.exports = { clearMemory };
