const fs = require('fs');
const path = require('path');

// Path to the memory_databases folder
const memoryDatabasesPath = path.join(__dirname, '../../persistentdata/memory_databases');

// Function to clear the memory_databases folder
function clearMemory() {
    return new Promise((resolve, reject) => {
        fs.rm(memoryDatabasesPath, { recursive: true, force: true }, (err) => {
            if (err) {
                console.error('Error clearing the memory_databases directory:', err);
                return reject(err);
            }
            console.log('Cleared the memory_databases directory.');

            // Recreate the memory_databases folder
            fs.mkdir(memoryDatabasesPath, { recursive: true }, (err) => {
                if (err) {
                    console.error('Error creating the memory_databases directory:', err);
                    return reject(err);
                }
                console.log('Recreated the memory_databases directory.');
                resolve();
            });
        });
    });
}

module.exports = { clearMemory };