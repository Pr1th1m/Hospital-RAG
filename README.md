# Product-RAG

A Retrieval-Augmented Generation (RAG) system for healthcare information management. It combines a FastAPI backend, a React (Vite) frontend, and a Pinecone vector database to enable intelligent natural-language querying of hospitals, departments, and doctors.

## 🏗️ Architecture

```
User ──► React Frontend ──► FastAPI Backend ──► Groq LLM (GPT-OSS-120B)
                                   │                    │
                                   ├── SQLAlchemy DB     │
                                   └── Pinecone VectorDB ◄── Cohere Embeddings (v4.0)
```

**Data flow on write:**
1. Admin adds a hospital / department / doctor via the API.
2. The entity is saved to the relational DB (SQLAlchemy).
3. The entity data (merged with related entities for context) is sent to the LLM via `transform_text`.
4. The LLM generates structured `page_content` + `metadata` JSON.
5. The result is embedded with Cohere and stored in Pinecone.

**Data flow on query:**
1. User sends a message via the chat UI.
2. Backend infers entity type and performs filtered similarity search on Pinecone.
3. Retrieved context is injected into the LLM prompt with the user's question.
4. LLM generates a grounded, context-based response (with optional web search fallback via Tavily).

## 🚀 Features

- **LLM-Powered Vector Indexing** — Uses system prompts + LLM to generate rich `page_content` and `metadata` for each entity before storing in Vector DB
- **Streaming Chat** — Real-time SSE streaming responses via `/chat/stream`
- **Web Search Fallback** — Tavily-powered web search for real-time queries (weather, news, etc.)
- **Admin Dashboard** — Token-based admin auth with CRUD for hospitals, departments, doctors
- **Smart Retrieval** — Entity-type inference from query to filter vector search results
- **City Hospital Lookup** — Direct DB lookup for "hospitals in \<city\>" style queries
- **Voice Input** — Whisper-powered audio transcription endpoint
- **API Key Rotation** — Automatic Groq API key fallback on rate limits
- **Docker Support** — `docker-compose.yml` for containerized deployment

## 📁 Project Structure

```
Product-Rag/
├── backend/
│   ├── database_models/          # SQLAlchemy ORM models
│   │   ├── base.py
│   │   ├── database_connection.py
│   │   ├── hospital_database_model.py
│   │   ├── department_database_model.py
│   │   └── doctor_database_model.py
│   ├── pydantic_models/          # Request/response validation
│   │   ├── hospital_model.py
│   │   ├── department_model.py
│   │   ├── doctor_model.py
│   │   └── chatmodel.py
│   ├── main.py                   # FastAPI application & routes
│   ├── vector_database.py        # LLM transform + Pinecone indexing
│   ├── system_prompt.py          # System prompts for LLM data transformation
│   ├── groq_client.py            # Groq client with API key rotation
│   ├── app.py                    # CLI chat interface + system prompt
│   ├── Dockerfile
│   ├── requirements.txt
│   └── .env
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── Landing.jsx       # Landing page
│   │   │   ├── Chat.jsx          # Chat interface with streaming
│   │   │   ├── Explore.jsx       # Browse hospitals/departments/doctors
│   │   │   ├── AdminLogin.jsx    # Admin authentication
│   │   │   └── AdminDashboard.jsx # CRUD management panel
│   │   ├── components/
│   │   │   ├── Navbar.jsx
│   │   │   ├── ProtectedRoute.jsx
│   │   │   └── Toast.jsx
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   └── index.css
│   └── package.json
├── docker-compose.yml
├── RAG/                          # Standalone RAG scripts
├── trial-rag/                    # Experimental RAG scripts
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
GROQ_API_KEY_BACKUP=your_backup_groq_key     # optional, for rate-limit fallback
COHERE_API_KEY=your_cohere_api_key
PINECONE_API_KEY=your_pinecone_api_key
PINECONE_INDEX_NAME=your_index_name
PINECONE_INDEX_NAME1=your_second_index_name
PINECONE_INDEX_NAME2=your_third_index_name
ADMIN_PASSWORD=your_admin_password
TAVILY_API_KEY=your_tavily_api_key            # optional, for web search
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
| `POST` | `/admin/login` | Admin login, returns JWT-style token |

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

### Vector Indexing Pipeline (`vector_database.py`)
- `transform_text(data, system_prompt)` — Sends entity data to the LLM with a system prompt, parses the JSON response, and stores it in Pinecone
- `add_json_to_vector_database(json_output)` — Handles both single objects and arrays from LLM output
- Uses **Cohere embed-v4.0** embeddings via `PineconeVectorStore`

### System Prompts (`system_prompt.py`)
- `system_prompt_hospital` — Generates hospital page_content + metadata
- `system_prompt_department` — Generates department page_content + metadata (with hospital context)
- `system_prompt_doctor` — Generates doctor page_content + metadata (with hospital + department context)
- `system_prompt_*_list` — Batch variants for processing lists of entities

### Groq Client (`groq_client.py`)
- `call_with_fallback(api_call)` — Executes API calls with automatic key rotation on rate limits
- Supports primary + backup API keys

### Chat Logic (`main.py`)
- **Entity-type inference** — Detects if query is about hospitals, departments, or doctors for filtered search
- **City hospital lookup** — Direct DB query for "hospitals in \<city\>" patterns
- **Web search detection** — Routes real-time queries (weather, news) to Tavily
- **Tool calling** — LLM can invoke `websearch` tool for live data

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
| `pydantic` | Data validation |
| `groq` | LLM API client |
| `langchain-pinecone` | Vector store |
| `langchain-cohere` | Embeddings |
| `cohere` | Cohere API client |
| `pinecone` | Vector database |
| `tavily-python` | Web search |
| `python-dotenv` | Env management |

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
