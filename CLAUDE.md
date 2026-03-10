# CLAUDE.md — Hospital-RAG Codebase Guide

This file provides AI assistants with a comprehensive understanding of this repository's structure, conventions, and development workflows.

---

## Project Overview

**Hospital-RAG** is a Retrieval-Augmented Generation (RAG) system for healthcare information management. It combines a FastAPI REST backend with a PostgreSQL relational database, a Pinecone vector database, Cohere embeddings, and a Groq-powered LLM to enable natural language querying over hospital, department, and doctor records.

---

## Repository Structure

```
Hospital-RAG/
├── README.md
├── CLAUDE.md                          # This file
└── backend/
    ├── main.py                        # FastAPI application (primary entry point)
    ├── app.py                         # CLI chat interface + system_prompt1 definition
    ├── vector_database.py             # Pinecone vector store, embeddings, transform_text
    ├── system_prompt.py               # LLM prompts for data transformation
    ├── requirements.txt               # Python dependencies
    ├── database_models/
    │   ├── base.py                    # SQLAlchemy declarative Base
    │   ├── database_connection.py     # DB engine + sessionmaker
    │   ├── hospital_database_model.py # Hospital ORM model
    │   ├── department_database_model.py # Department ORM model
    │   └── doctor_database_model.py   # Doctor ORM model
    └── pydantic_models/
        ├── hospital_model.py          # Hospital Pydantic validation model
        ├── department_model.py        # Department Pydantic validation model
        └── doctor_model.py            # Doctor Pydantic validation model
```

> **Note:** `pydantic_models/chatmodel.py` is imported by `main.py` (`ChatRequest`, `chat_sessions`) but does **not exist** yet. This is a known gap that will cause an `ImportError` on startup.

---

## Architecture

```
User / Client
      │
      ▼
FastAPI (main.py)          CLI (app.py)
      │                         │
      ├── PostgreSQL (SQLAlchemy ORM)
      │       hospital / department / doctor tables
      │
      ├── Pinecone (vector_database.py)
      │       index1  ← used for similarity_search in chat
      │       index   ← initialized but not actively used for search
      │
      ├── Cohere Embeddings (embed-v4.0)
      │       Converts text → 1024-dim vectors
      │
      └── Groq LLM (openai/gpt-oss-120b)
              ├── transform_text() — converts raw DB records to embeddable docs
              └── /chat endpoint — answers user questions with RAG context
                      └── Tavily tool — web search fallback
```

### RAG Data Flow

1. Data is **created** via `POST /hospitals`, `POST /departments`, `POST /doctors` (stored in PostgreSQL only).
2. Data is **indexed** into Pinecone when the corresponding `GET` endpoint is called (`GET /get_hospitals`, etc.), which triggers `transform_text()`.
3. `transform_text()` calls the Groq LLM with a strict system prompt to produce JSON with `page_content` (embeddable text) and `metadata` (filterable fields).
4. Those documents are added to the Pinecone vector store via `add_json_to_vector_database()`.
5. At **chat time**, `vector_store.similarity_search(query, k=7)` retrieves the top-7 relevant chunks, which are injected as context into the LLM prompt.

---

## Environment Variables

All environment variables must be defined in a `.env` file inside `backend/`. The app uses `python-dotenv` to load them.

| Variable | Required | Description |
|---|---|---|
| `GROQ_API_KEY` | Yes | Groq API key for LLM inference |
| `COHERE_API_KEY` | Yes | Cohere API key for embeddings |
| `PINECONE_API_KEY` | Yes | Pinecone API key |
| `PINECONE_INDEX_NAME` | Yes | Name of the first Pinecone index (initialized but not used for chat) |
| `PINECONE_INDEX_NAME1` | Yes | Name of the second Pinecone index (used for similarity_search in chat) |
| `DB_URL` | Yes | SQLAlchemy-compatible PostgreSQL URL, e.g. `postgresql://user:pass@host:5432/dbname` |
| `TAVILY_API_KEY` | Yes | Tavily API key for web search tool |

---

## Running the Application

All commands must be run from the `backend/` directory.

### FastAPI Server

```bash
cd backend
uvicorn main:app --reload
```

API available at `http://localhost:8000`. Interactive docs at `http://localhost:8000/docs`.

### CLI Chat Interface

```bash
cd backend
python app.py
```

Type questions at the `You:` prompt. Enter `bye` to exit.

---

## Installing Dependencies

```bash
cd backend
pip install -r requirements.txt
```

> **Warning:** `requirements.txt` is incomplete. The following packages are used in code but missing from the file:
> - `groq` — used in `main.py`, `app.py`, `vector_database.py`
> - `tavily-python` — used in `main.py`, `app.py`
>
> Install them manually: `pip install groq tavily-python`

---

## API Endpoints

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/` | Health check — returns `{"message": "backend Intigrated"}` |
| `GET` | `/health` | DB connectivity check + active session count |
| `POST` | `/hospitals` | Create a hospital (writes to PostgreSQL only) |
| `GET` | `/get_hospitals` | Fetch all hospitals + sync all to Pinecone vector DB |
| `POST` | `/departments` | Create a department (validates `hospital_id` exists) |
| `GET` | `/get_departments` | Fetch all departments + sync merged hospital+dept data to Pinecone |
| `POST` | `/doctors` | Create a doctor (validates `hospital_id` + `department_id` exist) |
| `GET` | `/get_doctors` | Fetch all doctors + sync merged hospital+dept+doctor data to Pinecone |
| `POST` | `/chat` | Send a message; returns `session_id` + `answer` |

### Chat Request/Response

```json
// POST /chat
// Request:
{ "message": "Which hospitals have emergency services?", "session_id": "optional-uuid" }

// Response:
{ "session_id": "generated-or-provided-uuid", "answer": "..." }
```

Omit `session_id` on the first message; a UUID will be auto-generated and returned for use in subsequent messages.

---

## Data Models

### Pydantic Models (API validation — `pydantic_models/`)

**Hospital**
```
hospital_name: str (required)
hospital_city: str (required)
hospital_area: Optional[str]
hospital_type: str (required)  # e.g. "multispeciality", "single speciality"
ownership: Optional[str]        # e.g. "government", "private"
total_beds: Optional[int >= 0]
icu_beds: Optional[int >= 0]
emergency: bool (required)
accreditations: Optional[List[str]] = []
```

**Department**
```
hospital_id: UUID (required — must reference an existing hospital)
department_name: str (required)  # e.g. "cardiology", "neurology"
services: Optional[List[str]] = []
icu_support: bool (required)
```

**Doctor**
```
hospital_id: UUID (required — must reference an existing hospital)
department_id: UUID (required — must reference an existing department)
doctor_name: str (required)
doctor_speciality: str (required)
doctor_experience: Optional[int >= 0]
doctor_qualifications: Optional[List[str]] = []
languages: Optional[List[str]] = []
opd_timing: Optional[str]
```

### SQLAlchemy Models (DB — `database_models/`)

Mirror the Pydantic models above with the following additions:
- All primary keys are `UUID` auto-generated at the DB layer (`default=uuid.uuid4`)
- `hospital_id`, `department_id` are `ForeignKey` references
- PostgreSQL `ARRAY(String)` is used for list fields (`accreditations`, `services`, `doctor_qualifications`, `languages`)

---

## Key Modules

### `vector_database.py`

- **`vector_store`** — `PineconeVectorStore` instance using `index1` and Cohere embeddings. Used for `similarity_search()` in chat.
- **`transform_text(data, system_prompt)`** — calls Groq LLM to convert raw data string into a JSON list of `{page_content, metadata}` objects, then calls `add_json_to_vector_database()`.
- **`add_json_to_vector_database(json_output)`** — iterates over the JSON list and adds each item as a LangChain `Document` to Pinecone.

### `system_prompt.py`

Contains six specialized LLM prompts, each enforcing strict JSON output:

| Prompt | Purpose |
|---|---|
| `system_prompt_hospital` | Single hospital → `[{page_content, metadata}]` |
| `system_prompt_department` | Single merged hospital+department record |
| `system_prompt_doctor` | Single merged hospital+department+doctor record |
| `system_prompt_hospital_list` | List of hospitals (batch) |
| `system_prompt_department_list` | List of merged department records (batch) |
| `system_prompt_doctor_list` | List of merged doctor records (batch) |

All prompts instruct the LLM to output **only** a JSON array — no markdown, no explanation. The output is parsed with `json.loads()`.

### `app.py`

- Defines **`system_prompt1`** — the chat assistant's system prompt. This is imported by `main.py`.
- Contains the standalone CLI **`main()`** loop.
- Duplicates the `websearch()` helper (also in `main.py`).

### `main.py`

- FastAPI app with all route handlers.
- Imports `system_prompt1` from `app.py`.
- Imports `ChatRequest` and `chat_sessions` from `pydantic_models.chatmodel` — **this file does not exist** and must be created.
- `chat_sessions` is an in-memory dict keyed by `session_id`; conversation history is not persisted across restarts.

---

## Known Issues / Gaps

1. **Missing `pydantic_models/chatmodel.py`** — `main.py` imports `ChatRequest` (a Pydantic model with `message: str` and `session_id: Optional[str]`) and `chat_sessions` (a `dict`) from this module. The file must be created before the server starts.

2. **Missing dependencies in `requirements.txt`** — `groq` and `tavily-python` are used but not listed. Add them.

3. **No test suite** — There are no tests, no `pytest` configuration, and no test fixtures.

4. **No Docker / deployment config** — No `Dockerfile`, `docker-compose.yml`, or CI/CD pipelines exist.

5. **Duplicate `websearch()` function** — Defined identically in both `app.py` and `main.py`.

6. **In-memory session state** — `chat_sessions` dict in `chatmodel.py` (once created) is in-process memory only. All chat history is lost on server restart.

7. **Sync-on-read pattern** — Calling `GET /get_hospitals` (etc.) re-indexes all records every time. This can cause duplicate documents in Pinecone if called multiple times. There is no deduplication or upsert logic.

---

## LLM Models

| Usage | Model |
|---|---|
| Data transformation (`transform_text`) | `openai/gpt-oss-120b` via Groq |
| Chat responses | `openai/gpt-oss-120b` via Groq (commented alternative: `llama-3.3-70b-versatile`) |
| Embeddings | Cohere `embed-v4.0` (1024 dimensions) |

Temperature is set to `0` for all LLM calls (deterministic outputs).

---

## Development Conventions

- **All Python files run from `backend/`** as the working directory. Imports are relative to `backend/` (e.g., `from pydantic_models.hospital_model import Hospital`).
- **Pydantic models** are used for API input validation; **SQLAlchemy models** are used for DB persistence. They are kept in sync manually — there is no auto-generation.
- **IDs are never provided by API callers** — `hospital_id`, `department_id`, `doctor_id` are auto-generated UUIDs at the DB layer. They are commented out in the Pydantic models.
- **Data merging for vector DB** happens at the API layer by combining `__dict__` of related ORM instances with Python's `|` operator (dict merge), before passing to `transform_text()`.
- **System prompts are strict** — they instruct the LLM to output only parseable JSON. Do not loosen these constraints; `json.loads()` will fail on any extra text.
- **No medical advice** — The chat assistant is explicitly instructed to refuse diagnosis, treatment, or prescription requests. Do not modify this safety behavior.

---

## Adding a New Entity Type

To add a new entity (e.g., `Ambulance`):

1. Create `database_models/ambulance_database_model.py` — SQLAlchemy model with UUID primary key and relevant ForeignKeys.
2. Create `pydantic_models/ambulance_model.py` — Pydantic model matching the DB schema (omit the auto-generated ID field).
3. Add system prompts to `system_prompt.py` for single and list transformation.
4. Add `POST /ambulances` and `GET /get_ambulances` routes in `main.py`.
5. The `GET` route should merge related entity data and call `transform_text()` with the appropriate prompt.
6. `Base.metadata.create_all(bind=engine)` in `main.py` will auto-create the new table on next startup.
