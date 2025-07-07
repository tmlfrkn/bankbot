# Implementation Progress Log (BankBot)

> Cumulative record of significant implementation steps completed during the July-07 coding session.

---

### 1. Authentication & Users
* Added JWT-based auth (`/auth/login`) with PyJWT
* Seed script (`scripts/seed_users.py`) resets **users** table and inserts 5 demo users (Public → Executive) matching Access-Matrix.
* Auth dependency (`get_current_token_payload`) decodes Bearer token for protected routes.

### 2. Access Matrix Core
* Centralised `ACCESS_MATRIX`, `AccessType`, `UserAccessLevel` enums in `app/models.py`.
* Helper `check_user_access()` used by services.

### 3. RAG Service Layer (`app/services/rag_service.py`)
* Sentence-Transformer embedder (cached).
* `vector_search()` → pgvector similarity query limited by allowed doc-types.
* `choose_content()` chooses Full / Summary / Relevant according to matrix.
* `build_context()` assembles context with citation tags.

### 4. RAG Routers (`/rag/*`)
* `/rag/retrieve` – returns top-k chunks the user may see. Implements:
  * 403 if allowed types empty or all chunks hidden.
  * Returns only accessible parts (Summary/Relevant trimmed).
* `/rag/answer` –
  * Summary/Relevant-only → returns context directly (no LLM).
  * Full access → builds context & calls Yi-1.5-9B via ctransformers.
  * 403 / 404 rules same as retrieve.
* Added rich DEBUG prints for tracing (allowed types, retrieved, context len, etc.).

### 5. Scripts / Demos
* `scripts/demo_matrix_responses.py` – same query via `/rag/answer` for 5 users → shows differing outputs/403.
* `scripts/demo_retrieve_matrix.py` – 5 queries × 5 users over `/rag/retrieve`, prints chunk counts & first citation.

### 6. Tests
* `app/tests/test_rag_routes.py` – integration test against live server for `/rag/retrieve`.
* `app/tests/test_rag_answer_matrix.py` – tests `/rag/answer` across users & queries, prints first 400 chars.

### 7. Misc
* `app/services/llm_service.py` – cached Yi model wrapper.
* Added DB summary vs full handling, improved SQL casts, Any(:types) usage.
* Added demo & progress logs.

---

Next steps
1. Add distance threshold or re-rank for irrelevant public chunks.
2. Persist audit logs and response times.
3. Containerise app (Dockerfile, docker-compose). 