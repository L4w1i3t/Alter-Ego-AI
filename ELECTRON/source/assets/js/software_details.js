async function showSoftwareDetails() {
    const details = await window.electronAPI.getSoftwareDetails();
    if (!details) {
      console.error('Failed to load software details.');
      return;
    }
  
    const detailsOverlay = document.createElement('div');
    detailsOverlay.classList.add('details-overlay');
  
    const detailsBox = document.createElement('div');
    detailsBox.classList.add('details-box');
  
    const title = document.createElement('h2');
    title.textContent = 'Software Details';
  
    const content = document.createElement('div');
    content.innerHTML = `
      <p><strong>Software Name:</strong> ${details.softwareName}</p>
      <p><strong>Version:</strong> ${details.version}</p>
      <p><strong>Developed By:</strong> ${details.developedBy}</p>
      <p><strong>Tools:</strong></p>
      <ul>
        ${details.tools.map(tool => `<li>${tool}</li>`).join('')}
      </ul>
      <p><strong>Credits:</strong></p>
      <ul>
        ${details.credits.map(credit => `<li>${credit}</li>`).join('')}
      </ul>
      <p><strong>Legal:</strong></p>
      <ul>
        ${details.legal.map(legal => `<li>${legal}</li>`).join('')}
      </ul>
      <p><strong>Known Issues:</strong></p>
      <ul>
        ${details.knownIssues.map(issue => `<li>${issue}</li>`).join('')}
      </ul>
    `;
  
    const closeBtn = document.createElement('button');
    closeBtn.textContent = 'Close';
    closeBtn.classList.add('close-details-btn');
  
    detailsBox.appendChild(title);
    detailsBox.appendChild(content);
    detailsBox.appendChild(closeBtn);
    detailsOverlay.appendChild(detailsBox);
    document.body.appendChild(detailsOverlay);
  
    closeBtn.addEventListener('click', () => {
      document.body.removeChild(detailsOverlay);
    });
  }
  
  // Expose the function to the global scope
  window.showSoftwareDetails = showSoftwareDetails;
  