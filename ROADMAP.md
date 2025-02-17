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
