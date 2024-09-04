const fs = require('fs');
const path = require('path');

// Function to create a button with an icon and event listener
function createButton(className, iconClass, label, onClick) {
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = className;
    btn.innerHTML = `<i class="${iconClass}"></i> ${label}`;
    btn.addEventListener('click', onClick);
    return btn;
}

// Function to add a new entry for various categories
function addEntry(containerId, placeholder) {
    const container = document.getElementById(containerId);
    
    const entryDiv = document.createElement('div');
    entryDiv.className = 'entry';
    
    const entryInput = document.createElement('input');
    entryInput.type = 'text';
    entryInput.placeholder = placeholder;
    entryInput.className = 'entry-input';
    
    const removeBtn = createButton('btn remove-entry', 'fas fa-minus', 'Remove', () => container.removeChild(entryDiv));
    
    entryDiv.appendChild(entryInput);
    entryDiv.appendChild(removeBtn);
    container.appendChild(entryDiv);
}

// Function to initialize addEntry event listeners
function initializeAddEntryButtons(entries) {
    entries.forEach(([buttonId, containerId, placeholder]) => {
        document.getElementById(buttonId).addEventListener('click', () => addEntry(containerId, placeholder));
    });
}

// List of buttons and containers for different categories
const entryButtons = [
    ['add-trait', 'traits-container', 'Enter trait'],
    ['add-tone', 'tone-container', 'Enter tone'],
    ['add-speechStyle', 'speechStyle-container', 'Enter speech style'],
    ['add-metaAwareness', 'metaAwareness-container', 'Enter meta awareness'],
    ['add-like', 'likes-container', 'Enter like'],
    ['add-dislike', 'dislikes-container', 'Enter dislike'],
    ['add-rule', 'rules-container', 'Enter rule'],
];

// Initialize add-entry buttons
initializeAddEntryButtons(entryButtons);

// Functions for Relationships
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
    
    const addRelBtn = createButton('btn add-relationship', 'fas fa-plus', 'Add Relationship', () => addRelationship(relationshipContainer));
    const removeGroupBtn = createButton('btn remove-group', 'fas fa-minus', 'Remove Group', () => container.removeChild(groupDiv));
    
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
    
    const removeRelBtn = createButton('btn remove-relationship', 'fas fa-minus', 'Remove', () => container.removeChild(relationshipDiv));
    
    relationshipDiv.appendChild(nameInput);
    relationshipDiv.appendChild(descInput);
    relationshipDiv.appendChild(removeRelBtn);
    
    container.appendChild(relationshipDiv);
}

// Helper function to collect form values and return as an array
function collectValues(selector) {
    return Array.from(document.querySelectorAll(selector)).map(input => input.value.trim()).filter(Boolean);
}

// Function to generate .chr content based on the user input
function generateChrFile() {
    const name = document.getElementById('name').value;
    const personality = document.getElementById('personality').value.trim();
    
    const traits = collectValues('#traits-container .entry-input');
    const tone = collectValues('#tone-container .entry-input');
    const speechStyle = collectValues('#speechStyle-container .entry-input');
    const metaAwareness = collectValues('#metaAwareness-container .entry-input');
    const likes = collectValues('#likes-container .entry-input');
    const dislikes = collectValues('#dislikes-container .entry-input');
    const rules = collectValues('#rules-container .entry-input');

    const relationshipGroups = document.querySelectorAll('.relationship-group');
    let relationships = '';
    let otherRelationships = '';

    relationshipGroups.forEach(group => {
        const groupName = group.querySelector('.relationship-group-name').value.trim();
        let groupContent = '';

        const relationshipEntries = group.querySelectorAll('.relationship-entry');
        relationshipEntries.forEach(entry => {
            const relName = entry.querySelector('.relationship-name').value.trim();
            const relDesc = entry.querySelector('.relationship-description').value.trim();
            groupContent += `        - ${relName}: ${relDesc}\n`;
        });

        if (groupName && groupContent) {
            relationships += `    {${groupName}}: \n${groupContent}`;
        } else if (groupContent) {
            otherRelationships += groupContent;
        }
    });

    if (otherRelationships) {
        relationships += `    {Other}: \n${otherRelationships}`;
    }

    let chrContent = '';

    // Dynamically add each section if it has content
    if (name) chrContent += `YOUR NAME IS: ${name}\n\n`;
    if (personality) chrContent += `[Personality]:\n    - ${personality.replace(/\n/g, '\n    - ')}\n\n`;
    if (traits.length) chrContent += `[Traits]:\n${traits.map(trait => `    - ${trait}`).join('\n')}\n\n`;
    if (tone.length) chrContent += `[Tone]:\n${tone.map(t => `    - ${t}`).join('\n')}\n\n`;
    if (speechStyle.length) chrContent += `[Speech Style]:\n${speechStyle.map(s => `    - ${s}`).join('\n')}\n\n`;
    if (metaAwareness.length) chrContent += `[Meta Awareness]:\n${metaAwareness.map(m => `    - ${m}`).join('\n')}\n\n`;
    if (relationships.trim()) chrContent += `[Relationships]:\n${relationships.trim()}\n\n`;
    if (likes.length) chrContent += `[Likes]:\n${likes.map(like => `    - ${like}`).join('\n')}\n\n`;
    if (dislikes.length) chrContent += `[Dislikes]:\n${dislikes.map(dislike => `    - ${dislike}`).join('\n')}\n\n`;
    if (rules.length) chrContent += `[When responding, you must follow these rules]:\n${rules.map(rule => `    - ${rule}`).join('\n')}\n\n`;

    document.getElementById('preview').innerText = chrContent;
    console.log("Generated content:", chrContent);
}

// Function to export the .chr file
function exportChrFile() {
    const content = document.getElementById('preview').innerText;
    if (!content.trim()) {
        alert('Please generate the .chr file first!');
        return;
    }

    const outputDir = path.join(__dirname, 'output');

    if (!fs.existsSync(outputDir)) {
        fs.mkdirSync(outputDir);
        console.log("Created output directory:", outputDir);
    }

    const filePath = path.join(outputDir, `${document.getElementById('name').value || 'character'}.chr`);
    fs.writeFileSync(filePath, content);
    console.log("File saved to:", filePath);
    alert(`File saved successfully to ${filePath}`);
}

// Attach event listeners for generating and exporting .chr files
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