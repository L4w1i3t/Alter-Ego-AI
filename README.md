---

<div align="center">
  <img src="logo.png" alt="ALTER EGO Logo" title="ALTER EGO Logo" />
</div>

---

# ALTER EGO

ALTER EGO is an interactive digital AI interface that brings any personality to life. Converse, learn, or just have fun chatting with historical figures, fictional characters, or entirely new creatures of your imagination.

***CURRENT VERSION: Alpha 1.0***

---

## Table of Contents

- [About ALTER EGO](#about-alter-ego)
- [Features](#features)
- [System Requirements](#system-requirements)
- [Setup](#setup)
- [Usage](#usage)
- [Known Issues](#known-issues)
- [Optimizations & Future Improvements](#optimizations--future-improvements)
- [Legal](#legal)
- [Credits](#credits)
- [Contact](#contact)

---

## About ALTER EGO

ALTER EGO is an AI platform built with Electron and Python that transforms how you interact with digital personas. The application leverages modern NLP models, emotion detection via roberta-base-go_emotions, and voice synthesis to create immersive, realistic conversations with customizable characters.

---

## Features

- **Customizable Personalities**:  
  Create, load, and switch between various personas. In addition to your custom characters, you can always revert to the default "ALTER EGO" persona.

- **Backend Model Selection**:  
  Choose your preferred language model backend:
  - **Ollama**: Open-source and zero-cost by default (lightweight as of now, with further testing and optimizations planned.)
  - **OpenAI GPT**: Robust responses (requires valid API key and is billed on a by-token basis. Use Responsibly.)

- **Dynamic Conversation Memory**:  
  Conversations are stored persistently (using JSON files and FAISS for indexing) to enable context-aware responses and retrieval of chat history.

- **Realistic Voice Generation**:  
  Enjoy lifelike responses via ElevenLabs text-to-speech synthesis.

- **Emotion Detection & Dynamic Avatars**:  
  An embedded roberta-base-go_emotions model detects emotional cues from both your inputs and the assistant's responses, with the avatar updating dynamically to reflect the current emotional tone.

- **Built-In Setup Wizard & Management Tools**:  
  A setup wizard checks for dependencies (including Python, required models, and packages) and auto-installs missing components where possible. In-app menus let you manage API keys, voice models, and personas.

- **Platform Support**:  
  *Currently, only a Windows build is officially available.* Linux-specific details have not yet been fully ironed out, but future updates and testing are planned to enhance cross-platform compatibility.

---

## System Requirements

### Minimum Requirements:

- **Processor**: Intel Core i3 (8th gen or newer) / AMD Ryzen 3 (Dual-core, 2.4+ GHz)
- **Memory**: 4 GB RAM 
- **Storage**: 2.5 GB available space (500 MB for application, 2 GB for models and data)
- **Graphics**: Integrated graphics
- **Internet**: 1+ Mbps connection (required for API access)
- **OS**: Windows 10 64-bit

### Recommended Requirements:

- **Processor**: Intel Core i5 (10th gen or newer) / AMD Ryzen 5 or better (Quad-core, 3.0+ GHz)
- **Memory**: 8-16 GB RAM
- **Storage**: 6+ GB available space on SSD
- **Graphics**: Dedicated GPU with 2+ GB VRAM (for using Ollama with larger models)
- **Internet**: 5+ Mbps stable connection
- **OS**: Windows 10/11 64-bit

---

## Setup

ALTER EGO is designed to be portable and run "out of the box." When you first launch the application, a setup wizard will perform several checks:

- **Python Environment**:  
  - On Windows, an embedded Python executable is used.
  - On Linux, the wizard attempts to locate system Python (or install Python3 if needed).

- **Dependency Installation**:  
  The wizard ensures that required packages (listed in `requirements.txt`) are installed and that local language models (for Ollama, roberta-base-go_emotions, and sentence-transformers) are downloaded and cached.

- **Ollama Model Setup**:  
  A temporary Ollama server is started to pull the necessary base language model. Once complete, the server is terminated.

Once the wizard finishes, you're ready to use ALTER EGO!

**Prerequisites**:
- Basic technical familiarity with language models and API integrations.
- Valid API keys for OpenAI and ElevenLabs if you wish to access those services.
- A capable system (GPU recommended for heavier loads).

If you encounter any issues during setup, please open an issue in the repository.

---

## Usage

1. **Launch the Application**:  
   Run the main script (e.g. your packaged ALTEREGO.exe) to launch ALTER EGO.

2. **Select Language Model**:  
   A popup will allow you to choose between the Ollama engine (default) and OpenAI GPT's API.

3. **Manage Personas**:  
   - Use the "Load Character" button to choose a custom persona or select the built-in "ALTER EGO" default.
   - You can create, edit, or delete personas via the "Manage Personas" option in the settings menu.

4. **Initiate Conversation**:  
   - Type your message into the query box and press Enter or click "Send Query."
   - The assistant processes your query using the selected language model and responds with text and synthesized voice.

5. **View Dynamic Responses**:  
   - Emotion detection results are displayed.
   - The avatar updates to reflect the emotional tone of the conversation.

6. **Additional Tools**:  
   The settings panel includes options to manage API keys, voice models, view chat history, and clear conversation memory.

*Note: Speech recognition is currently disabled and hidden from the UI until fully implemented.*

---

## Known Issues

- **Speech Recognition**:  
  Speech recognition functionality is currently disabled. Input is text-based only.

- **Linux Support**:  
  At this time, only a Windows build is officially available as Linux-specific details have not yet been fully resolved.

- **Resource Usage**:  
  Heavy language models or context windows may strain system resources. Future updates will focus on optimizing performance.

- **Server Warmup Issues**:  
  Some users may experience extended wait times during server warmup. Recent updates have improved progress visibility and added timeout handling to prevent indefinite waiting.

---

## Optimizations & Future Improvements

- **Performance Testing & Optimizations**:  
  Further testing is planned to optimize the Python server, language models, and overall UI responsiveness. This is a key reason why the current Ollama model is kept relatively lightweight (and quite inaccurate or incoherent). Expect improvements in caching, asynchronous processing, and resource management in future updates.

- **Enhanced Cross-Platform Support**:  
  While the Windows build is primary for now, additional work is planned to refine Linux support, including packaging and system-specific optimizations.

- **Additional Features**:  
  Upcoming enhancements include robust speech recognition, extended conversation memory, and more refined emotion detection and avatar dynamics.

---

## Tutorials and Additional Resources

There will eventually be detailed tutorials on setting up API keys, loading and training voice models, and fine-tuning the system's performance. In future updates, I'll provide step-by-step guides for maximizing ALTER EGO's capabilities.

---

## Legal

By using ALTER EGO, you agree to the following:

- **API Terms of Service**:
  - OpenAI: [Terms](https://openai.com/policies/terms-of-use)
  - ElevenLabs: [Terms](https://elevenlabs.io/terms)

- **Content Responsibility**:
  - Users are responsible for ensuring that generated content complies with applicable laws.
  - Do not use the software for harmful, unethical, or illegal activities.

- **Intellectual Property**:
  - Respect copyrights and trademarks when creating or interacting with personas.

- **Privacy**:
  - Be cautious when sharing personal data. The developer is not liable for data breaches resulting from misuse.

---

## Credits

- **OpenAI GPT**: [OpenAI](https://openai.com)
- **Ollama**: [Ollama GitHub](https://github.com/ollama/ollama)
- **ElevenLabs**: [ElevenLabs](https://www.elevenlabs.io)
- **roberta-base-go_emotions**: [Hugging Face](https://huggingface.co/SamLowe/roberta-base-go_emotions)
- **Sentence-Transformers (MiniLM-L6-v2)**: [Hugging Face](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2)
- **FAISS**: [FAISS GitHub](https://github.com/facebookresearch/faiss)
- **Electron & NodeJS**: [Electron](https://electronjs.org)

---

## Contact

For questions, suggestions, or contributions, please open an issue on the repository. Please note that I am a very busy person and may not always be immediately available, but I will do my best to respond in a timely manner.

---