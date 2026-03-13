# MedRAG

A full-stack Retrieval-Augmented Generation (RAG) system for healthcare information. It combines a FastAPI backend, a React (Vite) frontend, and Pinecone vector search to enable intelligent natural-language querying of hospitals, departments, and doctors.

## 🏗️ Architecture

```
User ──► React Frontend ──► FastAPI Backend ──► Groq LLM (GPT-OSS-120B)
                                   │                    │
                                   ├── PostgreSQL (SQLAlchemy)
                                   └── Pinecone VectorDB ◄── Cohere Embeddings (v4.0)
```

**Data flow on write:**
1. Admin adds a hospital / department / doctor via the API.
2. The entity is saved to PostgreSQL via SQLAlchemy.
3. Entity data (merged with related entities for context) is sent to the LLM via `transform_text`.
4. The LLM generates structured `page_content` + `metadata` JSON.
5. The result is embedded with Cohere and stored in Pinecone.

**Data flow on query:**
1. User sends a message via the chat UI.
2. Backend infers entity type and performs filtered similarity search on Pinecone.
3. Retrieved context is injected into the LLM prompt with the user's question.
4. LLM generates a grounded, context-based response (with optional web search fallback via Tavily).

## 🚀 Features

- **LLM-Powered Vector Indexing** — Uses system prompts + LLM to generate rich `page_content` and `metadata` for each entity before storing in Pinecone
- **Streaming Chat** — Real-time SSE streaming responses via `/chat/stream`
- **Web Search Fallback** — Tavily-powered web search for real-time queries (weather, news, etc.)
- **Admin Dashboard** — Token-based admin auth with CRUD for hospitals, departments, doctors
- **Smart Retrieval** — Entity-type inference from query to filter vector search results
- **City Hospital Lookup** — Direct DB lookup for "hospitals in \<city\>" style queries
- **Voice Input** — Whisper-powered audio transcription endpoint
- **API Key Rotation** — Automatic Groq API key fallback on rate limits
- **Docker Support** — `docker-compose.yml` with PostgreSQL + backend containerization

## 📁 Project Structure

```
MedRAG/
├── backend/
│   ├── routes/                    # FastAPI route handlers
│   │   ├── admin.py               # Login + reindex vector store
│   │   ├── chat.py                # /chat and /chat/stream endpoints
│   │   ├── hospitals.py           # Hospital CRUD
│   │   ├── departments.py         # Department CRUD
│   │   ├── doctors.py             # Doctor CRUD
│   │   └── health.py              # Health check endpoint
│   ├── services/                  # Business logic layer
│   │   ├── chat_service.py        # Chat orchestration, streaming, tool calls
│   │   ├── retrieval.py           # Entity inference + Pinecone similarity search
│   │   ├── web_search.py          # Tavily web search wrapper
│   │   └── admin.py               # Token issuing + verification
│   ├── database_models/           # SQLAlchemy ORM models
│   │   ├── base.py
│   │   ├── database_connection.py
│   │   ├── hospital_database_model.py
│   │   ├── department_database_model.py
│   │   └── doctor_database_model.py
│   ├── pydantic_models/           # Request/response validation
│   │   ├── hospital_model.py
│   │   ├── department_model.py
│   │   ├── doctor_model.py
│   │   └── chatmodel.py
│   ├── main.py                    # App entry point, CORS, router mounting
│   ├── config.py                  # Centralized env vars and constants
│   ├── vector_database.py         # LLM transform + Pinecone indexing
│   ├── system_prompt.py           # System prompts for LLM data transformation
│   ├── groq_client.py             # Groq client with API key rotation
│   ├── Dockerfile
│   ├── requirements.txt
│   └── .env
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── Landing.jsx        # Landing page
│   │   │   ├── Chat.jsx           # Chat interface with streaming
│   │   │   ├── Explore.jsx        # Browse hospitals/departments/doctors
│   │   │   ├── AdminLogin.jsx     # Admin authentication
│   │   │   └── AdminDashboard.jsx # CRUD management panel
│   │   ├── components/
│   │   │   ├── Navbar.jsx
│   │   │   ├── ProtectedRoute.jsx
│   │   │   └── Toast.jsx
│   │   ├── utils/
│   │   │   └── api.js             # Centralized API client
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   └── index.css
│   └── package.json
├── docker-compose.yml             # PostgreSQL + backend orchestration
├── AGENTS.md
├── CLAUDE.md
└── README.md
```

## 🛠️ Installation

### Prerequisites

- Python 3.8+
- Node.js 18+
- Pinecone account
- Groq API key
- Cohere API key
- Tavily API key (optional, for web search)

### Backend Setup

```bash
cd backend
pip install -r requirements.txt
```

Create a `.env` file in `/backend`:
```env
GROQ_API_KEY=your_groq_api_key
GROQ_API_KEY_BACKUP=your_backup_groq_key           # optional, for rate-limit fallback
COHERE_API_KEY=your_cohere_api_key
PINECONE_API_KEY=your_pinecone_api_key
PINECONE_INDEX_NAME=your_index_name
PINECONE_INDEX_NAME1=your_second_index_name
PINECONE_INDEX_NAME2=your_third_index_name
ADMIN_PASSWORD=your_admin_password
TAVILY_API_KEY=your_tavily_api_key                  # optional, for web search
DB_URL=postgresql://user:pass@localhost:5432/dbname  # optional, defaults to SQLite
RETRIEVAL_TOP_K=8                                   # optional, default 8
ADMIN_TOKEN_TTL_MINUTES=120                         # optional, default 120
```

### Frontend Setup

```bash
cd frontend
npm install
```

### Docker (optional)

```bash
docker compose up --build
```
This starts PostgreSQL and the backend automatically. The frontend must be run separately with `npm run dev`.

## 🚦 Usage

### Start Backend

```bash
cd backend
uvicorn main:app --reload
```
API available at `http://localhost:8000`

### Start Frontend

```bash
cd frontend
npm run dev
```
UI available at `http://localhost:5173`

## 📡 API Endpoints

### Auth
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/admin/login` | Admin login, returns bearer token |

### Hospital Management
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `POST` | `/hospitals` | Admin | Add hospital + index to vector DB |
| `GET` | `/get_hospitals` | — | List all hospitals |

### Department Management
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `POST` | `/departments` | Admin | Add department (merged with hospital data) + index |
| `GET` | `/get_departments` | — | List all departments |

### Doctor Management
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `POST` | `/doctors` | Admin | Add doctor (merged with hospital + dept data) + index |
| `GET` | `/get_doctors` | — | List all doctors |

### Chat
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/chat` | Send message, get full response |
| `POST` | `/chat/stream` | Send message, get SSE streamed response |

### Utilities
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `POST` | `/transcribe` | — | Transcribe audio via Whisper |
| `POST` | `/admin/reindex_vector_store` | Admin | Re-index all entities into vector DB |
| `GET` | `/health` | — | Health check (DB status, session count) |

## 🔧 Core Components

### Routes (`routes/`)
Thin FastAPI route handlers that delegate to services. Each file owns a single domain: `chat.py`, `hospitals.py`, `departments.py`, `doctors.py`, `admin.py`, `health.py`.

### Services (`services/`)
- **`chat_service.py`** — Orchestrates the full chat flow: city-hospital shortcuts, real-time web queries, RAG retrieval, LLM tool calling, and SSE streaming
- **`retrieval.py`** — Entity-type inference from queries, filtered Pinecone similarity search, and grounded prompt building
- **`web_search.py`** — Tavily web search wrapper for real-time queries
- **`admin.py`** — Token issuing and bearer token verification

### Config (`config.py`)
Centralized configuration loading all env vars (`RETRIEVAL_TOP_K`, `ADMIN_TOKEN_TTL_MINUTES`, `ADMIN_PASSWORD`, `TAVILY_API_KEY`) in one place.

### Vector Indexing Pipeline (`vector_database.py`)
- `transform_text(data, system_prompt)` — Sends entity data to the LLM with a system prompt, parses the JSON response, and stores it in Pinecone
- `add_json_to_vector_database(json_output)` — Handles both single objects and arrays from LLM output
- Uses **Cohere embed-v4.0** embeddings via `PineconeVectorStore`

### Groq Client (`groq_client.py`)
- `call_with_fallback(api_call)` — Executes API calls with automatic key rotation on rate limits
- Supports primary + backup API keys with configurable retry delay

### Frontend (`frontend/src/utils/api.js`)
Centralized API client with bearer token injection, configurable base URL via `VITE_API_URL` env var.

## 🧠 LLM & Models

| Purpose | Model |
|---------|-------|
| Chat & data transformation | `openai/gpt-oss-120b` (via Groq) |
| Audio transcription | `whisper-large-v3-turbo` (via Groq) |
| Embeddings | Cohere `embed-v4.0` |

## 🔒 Safety & Security

- **No medical advice** — Declines diagnosis, treatment, or prescription requests
- **Context-grounded responses** — Answers only from retrieved data for healthcare queries
- **Admin token auth** — Bearer token with configurable TTL for admin endpoints
- **No secrets in code** — All credentials via `.env`
- **Safe fallbacks** — Graceful error messages on rate limits and failures

## 📦 Dependencies

| Package | Purpose |
|---------|---------|
| `fastapi` | Web framework |
| `uvicorn` | ASGI server |
| `sqlalchemy` | ORM |
| `psycopg2-binary` | PostgreSQL driver |
| `pydantic` | Data validation |
| `groq` | LLM API client |
| `langchain-pinecone` | Vector store |
| `langchain-cohere` | Embeddings |
| `cohere` | Cohere API client |
| `pinecone` | Vector database |
| `tavily-python` | Web search |
| `python-dotenv` | Env management |
| `faker` | Test data generation |

## 📝 Example Queries

```
You: What hospitals are in Mumbai?
Assistant: Here are the hospitals in Mumbai from current data:
- Apollo Hospital (Andheri)
- Fortis Hospital (Mulund)
Total: 2 hospitals.

You: Which doctors specialize in cardiology?
Assistant: [Returns cardiologists with hospital, department, and experience details]

You: What's the weather today?
Assistant: [Uses web search to fetch live weather data]
```

## 🤝 Contributing

Contributions are welcome! Please review the [AGENTS.md](AGENTS.md) for coding guidelines and the change checklist before submitting PRs.

---

**Note**: This is a healthcare information system. It does not provide medical advice, diagnosis, or treatment. Always consult qualified healthcare professionals for medical concerns.
