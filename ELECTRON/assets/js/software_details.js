async function showSoftwareDetails() {
    const details = await window.electronAPI.getSoftwareDetails();
    if (!details) {
        alert('Failed to load software details.');
        return;
    }

    // Create the overlay for the modal
    const detailsOverlay = document.createElement('div');
    detailsOverlay.classList.add('details-overlay');
    
    // Create the modal box
    const detailsBox = document.createElement('div');
    detailsBox.classList.add('details-box');
    
    // Add content to the modal
    const title = document.createElement('h2');
    title.textContent = 'Software Details';
    
    const content = document.createElement('div');
    content.innerHTML = `
        <p><strong>Software Name:</strong> ${details.softwareName}</p>
        <p><strong>Version:</strong> ${details.version}</p>
        <p><strong>Developed By:</strong> ${details.developedBy}</p>
        <p><strong>Credits:</strong></p>
        <ul>
            ${details.credits.map(credit => `<li>${credit}</li>`).join('')}
        </ul>
        <p><strong>Legal:</strong></p>
        <ul>
            ${details.legal.map(legal => `<li>${legal}</li>`).join('')}
        </ul>
    `;
    
    // Close button
    const closeBtn = document.createElement('button');
    closeBtn.textContent = 'Close';
    closeBtn.classList.add('close-details-btn');
    
    // Assemble the modal
    detailsBox.appendChild(title);
    detailsBox.appendChild(content);
    detailsBox.appendChild(closeBtn);
    detailsOverlay.appendChild(detailsBox);
    document.body.appendChild(detailsOverlay);
    
    // Add event listener to close the modal
    closeBtn.addEventListener('click', () => {
        document.body.removeChild(detailsOverlay);
    });
}

// Expose the function to the global scope
window.showSoftwareDetails = showSoftwareDetails;
