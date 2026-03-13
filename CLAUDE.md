# CLAUDE.md - Product-Rag

Repository guidance for Claude and other coding assistants.

## Purpose
- Maintain a healthcare-focused RAG system for hospitals, departments, and doctors.
- Prioritize correctness, safety, and grounded answers.
- Never provide medical advice, diagnosis, or treatment instructions.

## Structure
- `backend/` - FastAPI app, models, retrieval, chat logic.
- `frontend/` - Vite and React client.
- `RAG/` - standalone scripts and experiments.
- `trial-rag/` - experimental code.

## Commands
- Backend: `cd backend` then `pip install -r requirements.txt` and `uvicorn main:app --reload`
- Frontend: `cd frontend` then `npm install` and `npm run dev`
- Frontend build: `cd frontend` then `npm.cmd run build`
- Docker: `docker compose up --build`

## Environment
- Expected in `backend/.env`: `GROQ_API_KEY`, `COHERE_API_KEY`, `PINECONE_API_KEY`, `PINECONE_INDEX_NAME`, `PINECONE_INDEX_NAME1`, `ADMIN_PASSWORD`
- Optional: `GROQ_API_KEY_BACKUP`, `TAVILY_API_KEY`
- Never commit secrets or real credentials.

## Rules
- Keep API contracts stable unless a breaking change is requested.
- Update SQLAlchemy and Pydantic models together when schema changes.
- Keep retrieval and safety behavior explicit.
- Protect admin and write flows.
- Do not remove healthcare safety constraints.

## Frontend
- Preserve mobile and desktop responsiveness.
- Avoid broken glyphs or unreadable UI text.
- Prefer theme-aware colors over hardcoded values.

## Done
- Requested change works end-to-end.
- No obvious regressions introduced.
- Project remains runnable with documented commands.
