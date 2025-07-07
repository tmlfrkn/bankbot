# BankBot – Multilingual RAG & Secure Knowledge API

An enterprise-grade AI assistant prototype for banking operations. BankBot combines a multilingual Retrieval-Augmented-Generation (RAG) pipeline with a FastAPI backend that enforces a **five-level access-matrix**, token-based authentication, and full conversation history.

---

## 1  High-Level Architecture

```
                           ┌────────────────────────┐
                           │  Frontend / Integrator │
                           └──────────┬─────────────┘
                                      │ REST/JSON (+ JWT)
                 ┌─────────────────────▼─────────────────────┐
                 │               FastAPI App                │
                 │                                           │
                 │  ┌──────────────┐   ┌──────────────────┐  │
                 │  │ /auth/login  │   │  /history/*      │  │
                 │  └──────────────┘   └──────────────────┘  │
                 │        ▲                   ▲              │
                 │        │                   │              │
                 │  ┌──────────────┐   ┌──────────────┐      │
                 │  │  /rag/**     │   │ Audit Logging │      │
                 │  └──────────────┘   └──────────────┘      │
                 │        │                   │              │
                 └────────┼───────────────────┼──────────────┘
                          │                   │
                          ▼                   ▼
            ┌─────────────────────┐   ┌────────────────────┐
            │  Vector Store (PG)  │   │   SQL Tables       │
            │  + pgvector         │   │  users, history…   │
            └─────────────────────┘   └────────────────────┘
```

* **Document pipeline** ingests multilingual PDFs/txt, generates summaries/labels via Yi-1.5-9B-Chat, creates 1024-dim embeddings (Sentence-Transformer multilingual-e5-large) and stores them in PostgreSQL + **pgvector**.
* **FastAPI backend** exposes RAG retrieval & answering endpoints and enforces **Access Matrix** rules at query-time.
* **JWT authentication** protects every endpoint except `/health` & `/auth/login`.
* **Query history** table persists every request/response (+ IP) grouped by `session_id`—users can list, inspect or delete prior conversations.

---

## 2  Access-Matrix

| Document Type           | Public (1) | Internal (2) | Confidential (3) | Restricted (4) | Executive (5) |
|-------------------------|-----------|--------------|------------------|----------------|---------------|
| Public Product Info     | Full      | Full         | Full             | Full           | Full          |
| Internal Procedures     | None      | Full         | Full             | Full           | Full          |
| Risk Models             | None      | None         | Full             | Summary        | Full          |
| Regulatory Docs         | None      | Summary      | Relevant         | Full           | Full          |
| Investigation Reports   | None      | None         | None             | None           | Full          |
| Executive Reports       | None      | None         | None             | Summary        | Full          |

Helpers in `app/models.py` map **user level → access type (none/summary/relevant/full)**.

---

## 3  Project Structure (key folders)

```
app/
  ├─ main.py            # FastAPI factory & router wiring
  ├─ models.py          # SQLAlchemy models inc. QueryHistory
  ├─ database.py        # async engine / session helpers
  ├─ config.py          # pydantic-based settings loader
  ├─ security.py        # PBKDF2 password hashing & JWT helpers
  ├─ dependencies.py    # FastAPI auth dependency
  ├─ routers/
  │    ├─ auth.py       # /auth/login
  │    ├─ rag.py        # /rag/retrieve & /rag/answer
  │    └─ history.py    # /history/… CRUD
  └─ services/
       ├─ rag_service.py     # Embedding & vector search helpers
       ├─ llm_service.py     # Yi-1.5-9B-Chat loading & async inference
       └─ history_service.py # QueryHistory CRUD helpers
```

---

## 4  API Reference

### Authentication
| Method | Path          | Body                          | Response |
|--------|--------------|------------------------------|----------|
| POST   | `/auth/login` | `{ "username", "password" }` | `{ access_token, token_type }` |

Token payload includes `username`, `access_level`, `role`.

### RAG Endpoints (protected)
| Method | Path             | Body                                         | Description |
|--------|------------------|----------------------------------------------|-------------|
| POST   | `/rag/retrieve`  | `{ query, session_id? }`                     | Returns top-3 accessible chunks w/ citations |
| POST   | `/rag/answer`    | `{ query, session_id? }`                     | Generates answer; if all chunks limited → returns direct concatenation instead of LLM |

### History Endpoints (protected)
| Method | Path                                   | Description |
|--------|----------------------------------------|-------------|
| GET    | `/history/sessions`                    | List user sessions with last query preview |
| GET    | `/history/sessions/{session_id}`       | Full conversation (newest first) |
| DELETE | `/history/sessions/{session_id}`       | Hard-delete a session |

Other:
* `GET /health` – health probe
* Interactive docs at `/docs` (Swagger) & `/redoc`

---

## 5  Setup & Running

### Prerequisites
* Python 3.10+
* PostgreSQL 13+ with `pgvector` extension
* (Optional) CUDA GPU for faster embeddings/LLM

### Environment Variables (`.env`)
```
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/bankbot
SECRET_KEY=change_me
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
HOST=0.0.0.0
PORT=8000
```

### Install & Run
```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# create DB & enable pgvector (see docs/ or initial .sql files)

# seed demo users
python scripts/seed_users.py

# launch server (auto-creates tables on first run)
uvicorn app.main:app --reload
```

---

## 6  Testing

* **Unit / integration tests** live in `app/tests/` and can be executed via:
  ```bash
  pytest -q
  ```
* Example notebooks & demo scripts under `deneme/` showcase multi-role queries.

---

## 7  Security Notes

* Passwords hashed with **PBKDF2-SHA256**.
* JWT secrets & DB creds **must** be stored securely (e.g. Docker secrets, Vault).
* Every request except `/auth/login`, `/health` passes through JWT dependency.
* Access checks occur per-chunk at query-time → zero-leakage guarantee.
* All queries logged with user-id + IP in `query_history` for auditing.

---

## 8  Performance Hints

* Adjust `pgvector` index `lists` value based on chunk volume.
* `SentenceTransformer` runs on GPU if available (`torch.cuda.is_available()`).
* Yi-1.5-9B-Chat loaded with `gpu_layers=50`; tweak for memory vs latency.

---

## 9  License & Credits


Powered by **FastAPI**, **SQLAlchemy**, **pgvector**, **Sentence-Transformers**, and **Yi-1.5-9B-Chat**.

> Built as part of a technical proficiency test & research prototype – **not** production-ready.
