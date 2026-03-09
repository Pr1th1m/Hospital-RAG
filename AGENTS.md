# AGENT GUIDE - Product-Rag

This file gives coding agents and contributors a fast, reliable way to work in this repository.

## Mission
- Maintain a healthcare-focused RAG system that stores structured data and answers queries using retrieval plus LLM.
- Prioritize correctness, safety, and traceability over cleverness.
- Do not generate medical advice, diagnosis, or treatment instructions.

## Repository Map
- `backend/` - FastAPI API, SQLAlchemy models, vector indexing, chat logic.
- `frontend/` - Vite plus React web app.
- `RAG/` and `trial-rag/` - standalone and experimental scripts.
- `docker-compose.yml` - local orchestration entrypoint.

## Runbook

### Backend
```powershell
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

### Frontend
```powershell
cd frontend
npm install
npm run dev
```

### Docker (optional)
```powershell
docker compose up --build
```

## Environment Variables
Expected in `backend/.env`:
- `GROQ_API_KEY`
- `COHERE_API_KEY`
- `PINECONE_API_KEY`
- `PINECONE_INDEX_NAME`
- `PINECONE_INDEX_NAME1` (if multi-index flow is used)

Never commit real keys.

## Coding Rules
- Keep API contracts stable unless explicitly changing client behavior.
- Add or update Pydantic and SQLAlchemy models together when schema changes.
- Keep retrieval and prompt safety logic explicit and avoid hidden side effects.
- Prefer small, composable functions over large route handlers.
- Keep error handling user-safe and developer-informative.

## Data and Safety Constraints
- Responses must be grounded in retrieved context for healthcare facts.
- Decline unsafe medical guidance requests.
- Do not log secrets or raw credentials.
- If uncertain about retrieved evidence, prefer a safe fallback response.

## Change Checklist
Before submitting changes:
1. Backend starts without import errors.
2. Frontend builds and runs.
3. Modified endpoints still return expected schema.
4. No secrets added to code, logs, or docs.
5. README and run commands remain accurate if tooling changed.

## When Making Bigger Changes
- Update `README.md` when setup, endpoints, or architecture changes.
- Document new env vars and migration steps.
- Add concise notes near non-obvious retrieval or prompt logic.

## Definition of Done
- Feature or bugfix works end-to-end.
- Safety behavior is preserved or improved.
- Local developer can run with documented commands only.
