#  E.V.O.N. — Enhanced Voice-Operated Nexus

A fully local, offline desktop AI assistant. Powered by open-source LLMs, Whisper STT, and Piper TTS — all running on your own hardware.

```
User Voice → Whisper (STT) → Ollama LLM → Piper TTS → Audio Output
```

---

##  Features

| Feature | Description |
|---------|-------------|
|  **Voice Input** | Record via microphone, transcribed locally by Whisper |
|  **Local LLM** | Llama 3 / Mistral via Ollama — no cloud, no API keys |
|  **Text-to-Speech** | Piper TTS (fast ONNX) with pyttsx3 fallback |
|  **Chat Mode** | Full ChatGPT-like text interface with streaming |
|  **Voice Mode** | End-to-end voice pipeline: speak → AI responds with audio |
|  **System Control** | Open Chrome, VSCode, File Explorer, etc. by voice/text |
|  **System Info** | CPU, RAM, GPU monitoring |
|  **Chat History** | SQLite-backed persistent conversations |
|  **Futuristic UI** | Dark theme, purple accents, animated waveforms |
|  **GPU Optimized** | Designed for RTX 3090 with float16 inference |

---

##  Project Structure

```
E.V.O.N./
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── config.py              # Pydantic settings (.env support)
│   │   ├── database.py            # Async SQLAlchemy + SQLite
│   │   ├── main.py                # FastAPI app + lifespan
│   │   ├── models.py              # ORM models + Pydantic schemas
│   │   ├── routers/
│   │   │   ├── __init__.py
│   │   │   ├── chat.py            # Chat endpoints (stream + non-stream)
│   │   │   ├── voice.py           # STT → LLM → TTS pipeline
│   │   │   └── system.py          # Open apps, system commands
│   │   └── services/
│   │       ├── __init__.py
│   │       ├── stt_service.py     # Whisper (faster-whisper)
│   │       ├── llm_service.py     # Ollama HTTP client
│   │       ├── tts_service.py     # Piper TTS + pyttsx3 fallback
│   │       └── system_service.py  # Windows app launcher
│   ├── data/                      # Auto-created: DB, uploads, TTS cache
│   ├── models/piper/              # Place Piper ONNX models here
│   ├── .env.example
│   ├── requirements.txt
│   └── run.py                     # Entry point
│
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── globals.css        # Tailwind + custom theme
│   │   │   ├── layout.tsx
│   │   │   └── page.tsx           # Main page
│   │   ├── components/
│   │   │   ├── ChatInterface.tsx   # Chat area + input
│   │   │   ├── MessageBubble.tsx   # Message rendering (Markdown)
│   │   │   ├── Sidebar.tsx         # Conversation list
│   │   │   ├── VoiceButton.tsx     # Animated mic button
│   │   │   └── Waveform.tsx        # Canvas audio visualizer
│   │   ├── hooks/
│   │   │   ├── useChat.ts          # Chat state + streaming
│   │   │   └── useVoice.ts         # Recording + voice pipeline
│   │   ├── lib/
│   │   │   └── api.ts              # API client functions
│   │   └── types/
│   │       └── index.ts            # TypeScript interfaces
│   ├── next.config.js
│   ├── tailwind.config.ts
│   ├── tsconfig.json
│   └── package.json
│
└── README.md
```

---

## 🛠️ Prerequisites

| Dependency | Version | Purpose |
|------------|---------|---------|
| **Python** | 3.11+ | Backend runtime |
| **Node.js** | 20+ | Frontend runtime |
| **Ollama** | Latest | Local LLM server |
| **CUDA Toolkit** | 12.x | GPU acceleration |
| **NVIDIA Driver** | 535+ | RTX 3090 support |

---

## Installation

### 1. Install Ollama & Pull a Model

```bash
# Download Ollama from https://ollama.com/download
# Then pull your preferred model:
ollama pull llama3
# or
ollama pull mistral
```

Verify Ollama is running:
```bash
ollama list
curl http://localhost:11434/api/tags
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# For CUDA GPU acceleration (RTX 3090):
pip install ctranslate2 --extra-index-url https://download.pytorch.org/whl/cu121

# Copy and configure environment
copy .env.example .env         # Windows
# cp .env.example .env         # macOS/Linux

# Edit .env to match your setup (model paths, GPU settings, etc.)
```

### 3. (Optional) Install Piper TTS

For high-quality offline TTS (recommended):

```bash
# Download Piper binary:
# https://github.com/rhasspy/piper/releases

# Download a voice model (place in backend/models/piper/):
# https://huggingface.co/rhasspy/piper-voices/tree/main
# Recommended: en_US-lessac-medium.onnx + .onnx.json

# Update PIPER_MODEL_PATH and PIPER_CONFIG_PATH in .env
```

If Piper is not installed, the system automatically falls back to **pyttsx3** (system TTS).

### 4. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Create environment file (optional)
echo NEXT_PUBLIC_API_URL=http://localhost:8000 > .env.local
```

---

## ▶️ Running

### Start Backend
```bash
cd backend
venv\Scripts\activate
python run.py
```
Backend starts at: **http://localhost:8000**
API docs at: **http://localhost:8000/docs**

### Start Frontend
```bash
cd frontend
npm run dev
```
Frontend starts at: **http://localhost:3000**

### Quick Start (both terminals)
```bash
# Terminal 1 — Backend
cd backend && venv\Scripts\activate && python run.py

# Terminal 2 — Frontend
cd frontend && npm run dev
```

---

## ⚙️ Configuration

All configuration is in `backend/.env`:

| Variable | Default | Description |
|----------|---------|-------------|
| `WHISPER_MODEL_SIZE` | `base` | `tiny`/`base`/`small`/`medium`/`large-v3` |
| `WHISPER_DEVICE` | `cuda` | `cuda` for GPU, `cpu` for CPU |
| `WHISPER_COMPUTE_TYPE` | `float16` | `float16` for GPU, `float32` for CPU |
| `OLLAMA_MODEL` | `llama3` | Any Ollama-supported model |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama server address |
| `OLLAMA_TIMEOUT` | `120` | Response timeout (seconds) |

### RTX 3090 Optimization

For best performance on RTX 3090 (24GB VRAM):

```env
WHISPER_MODEL_SIZE=large-v3
WHISPER_DEVICE=cuda
WHISPER_COMPUTE_TYPE=float16
OLLAMA_MODEL=llama3
```

The RTX 3090 can comfortably run:
- Whisper `large-v3` (~3 GB VRAM)
- Llama 3 8B via Ollama (~5-8 GB VRAM)
- Both simultaneously with room to spare

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/chat/` | Send message, get response |
| `POST` | `/api/chat/stream` | Stream response via SSE |
| `GET` | `/api/chat/conversations` | List all conversations |
| `GET` | `/api/chat/conversations/:id` | Get conversation + messages |
| `DELETE` | `/api/chat/conversations/:id` | Delete conversation |
| `POST` | `/api/voice/transcribe` | Audio → text (Whisper) |
| `POST` | `/api/voice/pipeline` | Full voice pipeline |
| `POST` | `/api/voice/pipeline/stream` | Streaming voice pipeline |
| `POST` | `/api/voice/tts` | Text → speech (WAV) |
| `POST` | `/api/system/open` | Open application |
| `POST` | `/api/system/command` | Run safe system command |
| `GET` | `/api/system/info` | System information |
| `GET` | `/api/system/apps` | List available apps |
| `GET` | `/api/health` | Health check |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Next.js Frontend                      │
│  ┌──────────┐ ┌──────────────┐ ┌─────────────────────┐ │
│  │ Sidebar  │ │ ChatInterface│ │  Waveform Visualizer│ │
│  └──────────┘ └──────────────┘ └─────────────────────┘ │
│         │              │                  │              │
│         └──────────────┼──────────────────┘              │
│                        │ HTTP / SSE                      │
└────────────────────────┼────────────────────────────────┘
                         │
┌────────────────────────┼────────────────────────────────┐
│                  FastAPI Backend                         │
│  ┌──────────┐ ┌──────────────┐ ┌──────────────────────┐│
│  │ Chat API │ │  Voice API   │ │    System API        ││
│  └────┬─────┘ └──────┬───────┘ └──────────┬───────────┘│
│       │              │                     │            │
│  ┌────┴──────────────┴─────────────────────┴──────────┐ │
│  │               Service Layer                        │ │
│  │  ┌─────────┐ ┌──────────┐ ┌─────┐ ┌────────────┐  │ │
│  │  │ Whisper │ │  Ollama  │ │ TTS │ │   System   │  │ │
│  │  │  (STT)  │ │  (LLM)  │ │     │ │  Commands  │  │ │
│  │  └─────────┘ └──────────┘ └─────┘ └────────────┘  │ │
│  └────────────────────────────────────────────────────┘ │
│                        │                                │
│  ┌─────────────────────┴──────────────────────────────┐ │
│  │              SQLite (aiosqlite)                     │ │
│  │         Conversations · Messages                    │ │
│  └────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

---

## 📝 License

MIT — use it however you like.
