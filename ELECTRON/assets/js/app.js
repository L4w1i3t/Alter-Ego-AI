document.addEventListener('DOMContentLoaded', () => {
    const srStatusEl = document.querySelector('.sr-status');
    const queryInputEl = document.querySelector('.query-input');
    const sendQueryBtn = document.querySelector('.send-query-btn');
    const menuIconEl = document.querySelector('.menu-icon');
    const settingsOverlay = document.querySelector('.settings-overlay');
    const settingsPanel = document.querySelector('.settings-panel');
    const closeSettingsBtn = document.querySelector('.close-settings-btn');
  
    // Initial state of speech recognition
    let srOn = false; // currently OFF (red)
  
    // Toggle Speech Recognition on F4 key
    document.addEventListener('keydown', (event) => {
      if (event.key === 'F4') {
        srOn = !srOn;
        updateSpeechRecognitionStatus();
      }
    });
  
    // Submit query on Send Query button click
    sendQueryBtn.addEventListener('click', submitQuery);
  
    // Submit query on Enter key in the query input field
    queryInputEl.addEventListener('keydown', (event) => {
      if (event.key === 'Enter') {
        submitQuery();
      }
    });
  
    function submitQuery() {
      const query = queryInputEl.value.trim();
      if (query) {
        // For now, just log the query
        console.log('Submitted Query:', query);
        queryInputEl.value = '';
      }
    }
  
    function updateSpeechRecognitionStatus() {
      srStatusEl.classList.remove('sr-on', 'sr-off');
      if (srOn) {
        srStatusEl.textContent = 'ON';
        srStatusEl.classList.add('sr-on');
      } else {
        srStatusEl.textContent = 'OFF';
        srStatusEl.classList.add('sr-off');
      }
    }
  
    // Show settings panel when menu icon is clicked
    menuIconEl.addEventListener('click', () => {
      settingsOverlay.style.display = 'flex';
    });
  
    // Close settings panel when close button is clicked
    closeSettingsBtn.addEventListener('click', () => {
      closeSettingsPanel();
    });
  
    // Close settings panel if user clicks outside the panel
    settingsOverlay.addEventListener('click', (event) => {
      if (event.target === settingsOverlay) {
        closeSettingsPanel();
      }
    });
  
    function closeSettingsPanel() {
      settingsOverlay.style.display = 'none';
    }

    // Add event listener for Clear Memory
    const clearMemoryOption = document.getElementById('clear-memory');
    clearMemoryOption.addEventListener('click', () => {
        // Show confirmation dialog
        showConfirmationDialog();
    });

    function showConfirmationDialog() {
        // Create a modal for confirmation
        const confirmationOverlay = document.createElement('div');
        confirmationOverlay.classList.add('confirmation-overlay');
        
        const confirmationBox = document.createElement('div');
        confirmationBox.classList.add('confirmation-box');
        
        const message = document.createElement('p');
        message.textContent = 'Are you sure you want to clear all memory? This action cannot be undone.';
        
        const buttonsDiv = document.createElement('div');
        buttonsDiv.classList.add('confirmation-buttons');
        
        const confirmBtn = document.createElement('button');
        confirmBtn.textContent = 'Yes';
        confirmBtn.classList.add('confirm-btn');
        
        const cancelBtn = document.createElement('button');
        cancelBtn.textContent = 'No';
        cancelBtn.classList.add('cancel-btn');
        
        buttonsDiv.appendChild(confirmBtn);
        buttonsDiv.appendChild(cancelBtn);
        
        confirmationBox.appendChild(message);
        confirmationBox.appendChild(buttonsDiv);
        confirmationOverlay.appendChild(confirmationBox);
        document.body.appendChild(confirmationOverlay);
        
        // Add styles for the confirmation dialog
        const style = document.createElement('style');
        style.textContent = `
            .confirmation-overlay {
                position: fixed;
                top: 0;
                left: 0;
                width: 100vw;
                height: 100vh;
                background: rgba(0, 0, 0, 0.8);
                display: flex;
                justify-content: center;
                align-items: center;
                z-index: 1000;
            }
            .confirmation-box {
                background: #000;
                border: 2px solid #0f0;
                padding: 2em;
                border-radius: 0.5em;
                text-align: center;
                color: #0f0;
                max-width: 400px;
                width: 90%;
            }
            .confirmation-buttons {
                margin-top: 1.5em;
                display: flex;
                justify-content: space-around;
            }
            .confirmation-buttons .confirm-btn,
            .confirmation-buttons .cancel-btn {
                padding: 0.5em 1em;
                border: 1px solid #0f0;
                background: #000;
                color: #0f0;
                cursor: pointer;
                border-radius: 0.2em;
                font-family: inherit;
            }
            .confirmation-buttons .confirm-btn:hover {
                background: #0f0;
                color: #000;
            }
            .confirmation-buttons .cancel-btn:hover {
                background: #0f0;
                color: #000;
            }
        `;
        document.head.appendChild(style);
        
        // Handle button clicks
        confirmBtn.addEventListener('click', () => {
            // Send IPC message to main process to clear memory
            window.electronAPI.clearMemory();
            // Remove the confirmation dialog
            document.body.removeChild(confirmationOverlay);
        });
        
        cancelBtn.addEventListener('click', () => {
            // Remove the confirmation dialog
            document.body.removeChild(confirmationOverlay);
        });
    }
    // Listen for memory clearing result
    window.electronAPI.onClearMemoryResult((event, data) => {
        showResultDialog(data.success, data.message);
    });

    function showResultDialog(success, message) {
        // Create a modal for the result
        const resultOverlay = document.createElement('div');
        resultOverlay.classList.add('result-overlay');
        
        const resultBox = document.createElement('div');
        resultBox.classList.add('result-box');
        
        const resultMessage = document.createElement('p');
        resultMessage.textContent = message;
        resultMessage.style.color = success ? '#0f0' : 'red';
        
        const closeBtn = document.createElement('button');
        closeBtn.textContent = 'OK';
        closeBtn.classList.add('close-result-btn');
        
        resultBox.appendChild(resultMessage);
        resultBox.appendChild(closeBtn);
        resultOverlay.appendChild(resultBox);
        document.body.appendChild(resultOverlay);
        
        // Add styles for the result dialog
        const style = document.createElement('style');
        style.textContent = `
            .result-overlay {
                position: fixed;
                top: 0;
                left: 0;
                width: 100vw;
                height: 100vh;
                background: rgba(0, 0, 0, 0.8);
                display: flex;
                justify-content: center;
                align-items: center;
                z-index: 1000;
            }
            .result-box {
                background: #000;
                border: 2px solid #0f0;
                padding: 2em;
                border-radius: 0.5em;
                text-align: center;
                color: #0f0;
                max-width: 400px;
                width: 90%;
            }
            .close-result-btn {
                margin-top: 1.5em;
                padding: 0.5em 1em;
                border: 1px solid #0f0;
                background: #000;
                color: #0f0;
                cursor: pointer;
                border-radius: 0.2em;
                font-family: inherit;
            }
            .close-result-btn:hover {
                background: #0f0;
                color: #000;
            }
        `;
        document.head.appendChild(style);
        
        // Handle button click
        closeBtn.addEventListener('click', () => {
            document.body.removeChild(resultOverlay);
        });
    }
    // Add event listener for Software Details
    const softwareDetailsOption = document.getElementById('software-details');
    softwareDetailsOption.addEventListener('click', () => {
        showSoftwareDetails();
    });
  });
