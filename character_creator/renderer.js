const fs = require('fs');
const path = require('path');

// Function to add a new entry for various categories
function addEntry(containerId, placeholder) {
    const container = document.getElementById(containerId);

    const entryDiv = document.createElement('div');
    entryDiv.className = 'entry';

    const entryInput = document.createElement('input');
    entryInput.type = 'text';
    entryInput.placeholder = placeholder;
    entryInput.className = 'entry-input';

    const removeBtn = document.createElement('button');
    removeBtn.type = 'button';
    removeBtn.className = 'btn remove-entry';
    removeBtn.innerHTML = '<i class="fas fa-minus"></i> Remove';
    removeBtn.addEventListener('click', () => container.removeChild(entryDiv));

    entryDiv.appendChild(entryInput);
    entryDiv.appendChild(removeBtn);

    container.appendChild(entryDiv);
}

// Attach event listeners for adding entries to various categories
document.getElementById('add-trait').addEventListener('click', () => addEntry('traits-container', 'Enter trait'));
document.getElementById('add-tone').addEventListener('click', () => addEntry('tone-container', 'Enter tone'));
document.getElementById('add-speechStyle').addEventListener('click', () => addEntry('speechStyle-container', 'Enter speech style'));
document.getElementById('add-metaAwareness').addEventListener('click', () => addEntry('metaAwareness-container', 'Enter meta awareness'));
document.getElementById('add-like').addEventListener('click', () => addEntry('likes-container', 'Enter like'));
document.getElementById('add-dislike').addEventListener('click', () => addEntry('dislikes-container', 'Enter dislike'));
document.getElementById('add-rule').addEventListener('click', () => addEntry('rules-container', 'Enter rule'));

// Functions for Relationships (unchanged)
document.getElementById('add-relationship-group').addEventListener('click', addRelationshipGroup);

function addRelationshipGroup() {
    const container = document.getElementById('relationships-container');

    const groupDiv = document.createElement('div');
    groupDiv.className = 'relationship-group';

    const groupNameInput = document.createElement('input');
    groupNameInput.type = 'text';
    groupNameInput.placeholder = 'Group Name (optional, e.g., SEES)';
    groupNameInput.className = 'relationship-group-name';

    const relationshipContainer = document.createElement('div');
    relationshipContainer.className = 'relationship-entries-container';

    const addRelBtn = document.createElement('button');
    addRelBtn.type = 'button';
    addRelBtn.className = 'btn add-relationship';
    addRelBtn.innerHTML = '<i class="fas fa-plus"></i> Add Relationship';
    addRelBtn.addEventListener('click', () => addRelationship(relationshipContainer));

    const removeGroupBtn = document.createElement('button');
    removeGroupBtn.type = 'button';
    removeGroupBtn.className = 'btn remove-group';
    removeGroupBtn.innerHTML = '<i class="fas fa-minus"></i> Remove Group';
    removeGroupBtn.addEventListener('click', () => container.removeChild(groupDiv));

    groupDiv.appendChild(groupNameInput);
    groupDiv.appendChild(relationshipContainer);
    groupDiv.appendChild(addRelBtn);
    groupDiv.appendChild(removeGroupBtn);

    container.appendChild(groupDiv);
}

function addRelationship(container) {
    const relationshipDiv = document.createElement('div');
    relationshipDiv.className = 'relationship-entry';

    const nameInput = document.createElement('input');
    nameInput.type = 'text';
    nameInput.placeholder = 'Relationship Name (e.g., Makoto Yuki)';
    nameInput.className = 'relationship-name';

    const descInput = document.createElement('textarea');
    descInput.placeholder = 'Relationship Description (e.g., Classmate, carries death, etc.)';
    descInput.className = 'relationship-description';

    const removeRelBtn = document.createElement('button');
    removeRelBtn.type = 'button';
    removeRelBtn.className = 'btn remove-relationship';
    removeRelBtn.innerHTML = '<i class="fas fa-minus"></i> Remove';
    removeRelBtn.addEventListener('click', () => container.removeChild(relationshipDiv));

    relationshipDiv.appendChild(nameInput);
    relationshipDiv.appendChild(descInput);
    relationshipDiv.appendChild(removeRelBtn);

    container.appendChild(relationshipDiv);
}

// Function to generate .chr content based on the user input
function generateChrFile() {
    console.log("Generate button clicked");
    const name = document.getElementById('name').value;
    const personality = document.getElementById('personality').value.split('\n').map(line => `    - ${line}`).join('\n');
    const age = document.getElementById('age').value.split('\n').map(line => `    - ${line}`).join('\n');
    const traits = Array.from(document.querySelectorAll('#traits-container .entry-input')).map(input => `    - ${input.value}`).join('\n');
    const tone = Array.from(document.querySelectorAll('#tone-container .entry-input')).map(input => `    - ${input.value}`).join('\n');
    const speechStyle = Array.from(document.querySelectorAll('#speechStyle-container .entry-input')).map(input => `    - ${input.value}`).join('\n');
    const metaAwareness = Array.from(document.querySelectorAll('#metaAwareness-container .entry-input')).map(input => `    - ${input.value}`).join('\n');
    const likes = Array.from(document.querySelectorAll('#likes-container .entry-input')).map(input => `    - ${input.value}`).join('\n');
    const dislikes = Array.from(document.querySelectorAll('#dislikes-container .entry-input')).map(input => `    - ${input.value}`).join('\n');
    const rules = Array.from(document.querySelectorAll('#rules-container .entry-input')).map(input => `    - ${input.value}`).join('\n');

    // Process Relationship Groups
    const relationshipGroups = document.querySelectorAll('.relationship-group');
    let relationships = '';
    let otherRelationships = '';

    relationshipGroups.forEach(group => {
        const groupName = group.querySelector('.relationship-group-name').value.trim();
        let groupContent = '';

        const relationshipEntries = group.querySelectorAll('.relationship-entry');
        relationshipEntries.forEach(entry => {
            const relName = entry.querySelector('.relationship-name').value;
            const relDesc = entry.querySelector('.relationship-description').value;
            groupContent += `        - ${relName}: ${relDesc}\n`;
        });

        if (groupName) {
            relationships += `    {${groupName}}: \n${groupContent}`;
        } else {
            otherRelationships += groupContent;
        }
    });

    // If there are relationships without a group, put them under "Other"
    if (otherRelationships) {
        relationships += `    {Other}: \n${otherRelationships}`;
    }

    const chrContent = `NAME: ${name}

[Personality]: 
${personality}

[Traits]: 
${traits}

[Tone]: 
${tone}

[Age]: 
${age}

[Speech Style]: 
${speechStyle}

[Meta Awareness]: 
${metaAwareness}

[Relationships]: 
${relationships.trim()}

[Likes]: 
${likes}

[Dislikes]: 
${dislikes}

[When responding, you must follow these rules]: 
${rules}`;

    document.getElementById('preview').innerText = chrContent;
    console.log("Generated content:", chrContent);
}

// Function to export the .chr file
function exportChrFile() {
    console.log("Export button clicked");
    const content = document.getElementById('preview').innerText;
    if (!content.trim()) {
        alert('Please generate the .chr file first!');
        return;
    }

    const outputDir = path.join(__dirname, 'output');

    // Create output directory if it doesn't exist
    if (!fs.existsSync(outputDir)) {
        fs.mkdirSync(outputDir);
        console.log("Created output directory:", outputDir);
    }

    const filePath = path.join(outputDir, `${document.getElementById('name').value || 'character'}.chr`);

    fs.writeFileSync(filePath, content);
    console.log("File saved to:", filePath);
    alert(`File saved successfully to ${filePath}`);
}

document.getElementById('generate').addEventListener('click', generateChrFile);
document.getElementById('export').addEventListener('click', exportChrFile);

// Tab switching logic
document.querySelectorAll('.tab').forEach(tab => {
    tab.addEventListener('click', function() {
        document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
        document.querySelectorAll('.tab-content').forEach(tc => tc.classList.remove('active'));

        this.classList.add('active');
        document.getElementById(this.getAttribute('data-tab')).classList.add('active');
    });
});
