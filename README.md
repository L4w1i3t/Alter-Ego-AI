---

<div align="center">
  <img src="logo.png" alt="ALTER EGO Logo" title="ALTER EGO Logo" />
</div>

---

# ALTER EGO

ALTER EGO is an Electron-based AI interface for creating and conversing with digital personas. The system uses a local Llama-based model via Ollama for text generation and employs an ONNX version of roberta-base-go_emotions for emotion detection. The application is designed to offer an engaging experience with dynamic personas, emotion-tracking avatars, and persistent chat histories.

***CURRENT VERSION: Alpha 1.0***

---

## Table of Contents

- [About ALTER EGO](#about-alter-ego)
- [Features](#features)
- [Setup](#setup)
- [Usage](#usage)
- [Known Issues](#known-issues)
- [Future Plans](#future-plans)
- [Legal](#legal)
- [Credits](#credits)
- [Contact](#contact)

---

## About ALTER EGO

Originally combining Electron with Python backends and ElevenLabs TTS, ALTER EGO now operates purely under Electron/Node. It runs a local Llama-based model via Ollama’s binaries—allowing offline or private usage—and integrates roberta-base-go_emotions for emotion detection. Text-to-Speech and speech recognition are currently disabled, though references remain in the code for potential reactivation in future versions.

**Tech Stack**
- Electron (Node/JavaScript)
- Local Llama-based Model: artifish/llama3.2-uncensored loaded through Ollama
- Hugging Face Transformers (ONNX) for emotion detection
- Persistent Data: JSON-based chat logs (per persona), local persona .chr files

---

## Features

- **Customizable Personalities**:  
  Create, load, and switch between various personas. In addition to your custom characters, you can always revert to the default “ALTER EGO” persona.

- **Local Llama Model Integration (Ollama)**
  By default, ALTER EGO uses a local Llama-based model. On first run, the Ollama executable pulls and caches the required model artifacts.

- **Emotion Detection & Dynamic Avatars**:  
  An embedded roberta-base-go_emotions model detects emotional cues from both your inputs and the assistant’s responses, with the avatar updating dynamically to reflect the current emotional tone.
  
- **Persistent Chat History**:  
  Each persona’s conversation history is saved in simple JSON files, so you can revisit or review any persona’s logs at any time.

- **Built-In Manager UIs**:  
  Manage personas, view chat history, clear memory, and more via in-app overlay panels.

---

## Setup

ALTER EGO is designed to be portable and run “out of the box.” When you first launch the application, the splash screen will pull necessary artifacts and dependencies automatically (this may take a few minutes.)

Once the pull finishes, you’re ready to use ALTER EGO!

**Prerequisites**:
- Basic technical familiarity with language models and API integrations.
- At least 8GB of storage.
- A capable system (I'll be frank, this needs testing).

If you encounter any issues during setup, please open an issue in the repository.

---

## Usage

1. **Launch the Application**:  
   Run the main script (e.g. your packaged ALTEREGO.exe) to launch ALTER EGO.

2. **Let the splash screen run**:  
   This is necessary

3. **Manage Personas**:  
   - Use the “Load Character” button to choose a custom persona or select the built-in “ALTER EGO” default.
   - You can create, edit, or delete personas via the “Manage Personas” option in the settings menu.

4. **Initiate Conversation**:  
   - Type your message into the query box and press Enter or click “Send Query.”
   - The program processes your query using the selected language model and responds with markdown text.

5. **View Dynamic Responses**:  
   - Emotion detection results are displayed.
   - The avatar updates to reflect the emotional tone of the conversation.

---

## Known Issues

- **No TTS / Speech Recognition**:  
  Voice features have been removed or disabled in this alpha release, as some backend logic is being overhauled.

- **Windows-Focused**:  
  Limited testing has been done on other platforms. Ollama is also somewhat platform-specific; building from source on macOS or Linux requires additional steps not yet fully documented here.

- **Model Instabilities**:
  The included model may produce repetitive or incoherent replies, as this is a relatively lightweight model currently used for testing purposes. Tweaking or swapping the base model might require advanced steps or a custom build.

- **Memory Mechanisms**:
  While chat logs persist, short-term or vector-based memory is not fully implemented in this alpha; references to FAISS usage are placeholders left from earlier versions.

- **Resource Usage**:  
  Heavy language models or context windows may strain system resources. Future updates will focus on optimizing performance.

---

## Future Plans

- **Reintroduce missing features**:
  Add back TTS and SR logic that minimizes latency.

- **Extend Memory**:
  Expand conversation memory with short-term retrieval or vector databases, once the local approach stabilizes.

- **Enhanced Cross-Platform Support**:  
  While the Windows build is primary for now, additional work is planned to refine Linux support, including packaging and system-specific optimizations.

---

## Tutorials and Additional Resources

There will eventually be detailed tutorials on setting up API keys, loading and training voice models, and fine-tuning the system’s performance. In future updates, I'll provide step-by-step guides and additional resources to help you get the most out of ALTER EGO.

---

## Legal

By using ALTER EGO, you agree to the following:

- **Content Responsibility**:
  - Users are responsible for ensuring that generated content complies with applicable laws.
  - Do not use the software for harmful, unethical, or illegal activities.

- **Intellectual Property**:
  - Respect copyrights and trademarks when creating or interacting with personas.

- **Third-Party Tools**:
  - Ollama, roberta-base-go_emotions, Node/Electron, etc. remain the property of their respective authors.

- **Privacy**:
  - Be cautious when sharing personal data. The developer is not liable for data breaches resulting from misuse.

---

## Credits

- **Ollama**: [Ollama GitHub](https://github.com/ollama/ollama)
- **roberta-base-go_emotions**: [Hugging Face](https://huggingface.co/SamLowe/roberta-base-go_emotions)
- **Electron & NodeJS**: [Electron](https://electronjs.org)

---

## Contact

Please open an issue or pull request if you find bugs or want to contribute. Due to a busy schedule and being a one-man team, responses may not be immediate, but all feedback is welcome. Enjoy experimenting with ALTER EGO, and thank you for your understanding as the project evolves.

---