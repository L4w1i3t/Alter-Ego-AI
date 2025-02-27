async function showChatHistory() {
  // 1) Figure out which persona is currently active
  const activeCharacterEl = document.querySelector(".active-character");
  const personaName = activeCharacterEl?.textContent.trim() || "DEFAULT";

  // 2) IPC call to get the logs from the main process
  const result = await window.electronAPI.getChatHistory(personaName);
  if (!result.success) {
    console.error("Failed to load chat history for:", personaName);
    return;
  }
  const historyArray = result.history; // Array of {timestamp, role, content}

  // 3) Build overlay
  const overlay = document.createElement("div");
  overlay.classList.add("chat-history-overlay");

  // The main box
  const box = document.createElement("div");
  box.classList.add("chat-history-box");

  // Title
  const title = document.createElement("h2");
  title.textContent = `Chat History: ${personaName}`;
  box.appendChild(title);

  // A scrollable container for messages
  const messagesContainer = document.createElement("div");
  messagesContainer.classList.add("chat-messages-container");
  box.appendChild(messagesContainer);

  // 4) Render each message using a DocumentFragment for efficiency
  const fragment = document.createDocumentFragment();
  historyArray.forEach((msg) => {
    const msgDiv = document.createElement("div");
    msgDiv.classList.add("chat-message");
    // Decide color based on msg.role
    if (msg.role === "user") {
      msgDiv.classList.add("user-message"); // user = white text bubble
    } else {
      msgDiv.classList.add("assistant-message"); // assistant = blue text bubble
    }

    // Format: timestamp in small font, then the text
    const timeP = document.createElement("p");
    timeP.classList.add("chat-timestamp");
    timeP.textContent = `[${msg.timestamp}]`;

    const contentP = document.createElement("p");
    contentP.classList.add("chat-content");
    contentP.textContent = msg.content;

    msgDiv.appendChild(timeP);
    msgDiv.appendChild(contentP);
    fragment.appendChild(msgDiv);
  });
  messagesContainer.appendChild(fragment);

  // 5) Close button
  const closeBtn = document.createElement("button");
  closeBtn.textContent = "Close";
  closeBtn.classList.add("close-chat-history-btn");
  closeBtn.addEventListener("click", () => {
    document.body.removeChild(overlay);
  });
  box.appendChild(closeBtn);

  // Add box to overlay, overlay to DOM
  overlay.appendChild(box);
  document.body.appendChild(overlay);
}

// Expose it globally so other scripts can call `window.showChatHistory()`
window.showChatHistory = showChatHistory;
