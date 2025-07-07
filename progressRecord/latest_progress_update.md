# Progress Update – Phase III (July 2025)

> This log records everything completed **after** the initial prototype, up to the current commit.

## 1  Access-Matrix Enforcement
* Implemented five-level access matrix (`AccessType` + `ACCESS_MATRIX` helper) in `app/models.py`.
* RAG endpoints now dynamically choose `summary`, `relevant` or `full` chunk content depending on user level.
* Added robust 403/404 handling with explicit debug prints.

## 2  Authentication & Demo Users
* Added `/auth/login` router with JWT (PyJWT) + PBKDF2 password hashing.
* `scripts/seed_users.py` wipes tables and seeds five demo users (public → executive) for matrix testing.

## 3  RAG Pipeline Improvements
* **Model switch:** original Mistral-7B summaries performed poorly for multilingual (French & Turkish) content. Replaced with **Yi-1.5-9B-Chat** loaded via `ctransformers`; quality markedly improved (especially FR/TUR ↔ EN queries).
* Embeddings remain on `intfloat/multilingual-e5-large` (1024-d) – still best X-lingual recall after tests.
* `rag_service.py` embeds asynchronously (`asyncio.to_thread`) and caches the model.

## 4  Query History & Auditing
* New `QueryHistory` table (SQLAlchemy) storing: user, session_id, route, query, response_text, IP, timestamp.
* Service & router layer (`history_service.py`, `/history/*`) allow users to list, fetch and delete conversation sessions.
* `rag` router now saves every `/retrieve` and `/answer` call – fully auditable trace.

## 5  README & Docs Refresh
* Comprehensive `README.md` rewritten – includes architecture diagram, API reference, setup, security, performance tips.
* Added `.gitignore` ignoring `venv/`, `models/`, build artefacts etc.
* Progress docs under `progressRecord/` kept in sync.

## 6  Upcoming
* Integrate streaming responses for LLM answers (Server-Sent Events).
* Add unit coverage for `/history/*` endpoints.
* Evaluate GPU quantisation tweaks (Yi Q4_K_M vs Q6_K) vs latency.

---
_Last updated: **{{date}}**_ 