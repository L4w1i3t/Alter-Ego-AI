flowchart LR
    subgraph Start
        A[npmstart.bat / npm start script]
    end

    A -->|Launches Electron| B[main.js]

    subgraph "Main Process (backend)"
        B --> C[ipcHandlers.js]
        C --> D[api/localLogic.js]
        C --> E[api/goEmotionsLogic.js]
        C --> H[assets/js/memory_manager.js]
        C -->|"Manages persona files and keys"| G[utils.js]
    end

    subgraph "Renderer (frontend)"
        F[preload.js <br>(Context Bridge)] --> I[index.html]
        I --> J[assets/js/app.js <br>(Core UI logic)]
        J --> K[assets/js/splash.js <br>(Splash Screen)]
        J --> L[assets/js/software_details.js]
        J --> M[assets/js/persona_manager.js]
        J --> N[assets/js/chat_history.js]
        J --> O[assets/js/api_key_manager.js]
    end

    B -->|Creates BrowserWindow| F
    F -->|Exposed APIs| J
    J -->|IPC calls| C
    H -->|Save & Load chat logs| persistentdata([persistentdata/memory_databases])
    G -->|Reading & writing persona <br> and keys data| persistentdata_2([persistentdata/personas, keys.json])

sequenceDiagram
    autonumber
    participant User
    participant Frontend as Program UI
    participant Ollama as Ollama (LLM)
    participant Emotions as Emotion Detector
    participant TTS as ElevenLabs TTS (not impl. as streaming)
    participant STM as Short-Term Memory (not impl. yet)
    participant LTM as Long-Term Memory (not impl. yet)

    User->>Frontend: Boot the program
    Note left of Frontend: (Wait for initialization, splash screen, etc.)
    Frontend->>Frontend: Load or default persona<br/>(User may also choose one)
    Frontend->>Frontend: (Optional) Select Voice Model (not impl. yet)

    loop For each user query
        User->>Frontend: Enter query
        Frontend->>Emotions: Detect user emotions
        Emotions-->>Frontend: Return emotion scores for user
        Frontend->>Ollama: Send query to Ollama LLM

        Ollama-->>Frontend: Once done, return full response text

        Frontend->>Frontend: Display final text in response box

        alt Voice model loaded?
            Frontend->>TTS: Send text for TTS/streaming
            TTS-->>Frontend: Return audio stream
            Note over Frontend: Speech is played in sync with final text
        else
            Note over Frontend: Skips TTS step
        end

        par Memory
            Frontend->>STM: (not impl.) Push interaction to STM buffer<br/>(pop oldest if > 3)
            Frontend->>LTM: (not impl.) Save to LTM & embed<br/>find top-3 relevant old logs
            Frontend->>Frontend: Chat memory is saved locally
        end

        Frontend->>Emotions: Detect response emotions
        Emotions-->>Frontend: Return emotion scores for response
        User->>Frontend: Sees final text (and hears speech if TTS)
    end
