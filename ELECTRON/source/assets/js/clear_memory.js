const fs = require('fs');
const path = require('path');

// Path to the memory_databases folder
const memoryDatabasesPath = path.join(__dirname, '../../persistentdata/memory_databases');

// Function to clear the memory_databases folder
function clearMemory() {
    return new Promise((resolve, reject) => {
        fs.readdir(memoryDatabasesPath, (err, files) => {
            if (err) {
                console.error('Error reading the memory_databases directory:', err);
                return reject(err);
            }

            // Iterate over each file in the directory
            let deletePromises = files.map(file => {
                return new Promise((res, rej) => {
                    const filePath = path.join(memoryDatabasesPath, file);
                    fs.unlink(filePath, (err) => {
                        if (err) {
                            console.error('Error deleting file:', filePath, err);
                            rej(err);
                        } else {
                            console.log('Deleted file:', filePath);
                            res();
                        }
                    });
                });
            });

            Promise.all(deletePromises)
                .then(() => resolve())
                .catch(reject);
        });
    });
}

module.exports = { clearMemory };
