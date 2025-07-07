# BankBot REST API – Quick Reference

This document lists all public routes exposed by the FastAPI backend and how to integrate them from a frontend or external service.

> Base URL examples assume local Docker run on `http://localhost:8000`. Adjust accordingly for prod.

---

## 1. Health Check
| Method | Path        | Auth | Body | Response |
|--------|-------------|------|------|----------|
| GET    | `/health`   | ❌    | —    | `{ "status": "ok" }` |

Simple liveness probe; useful for load-balancers / CI.

---

## 2. Authentication
| Method | Path            | Auth | Body (JSON)                          | Response (200) |
|--------|-----------------|------|--------------------------------------|----------------|
| POST   | `/auth/login`   | ❌    | `{ "username": "alice", "password": "…" }` | `{ "access_token": "jwt…", "token_type": "bearer" }` |

Save `access_token` and send it via `Authorization: Bearer <token>` header for **all** protected routes.

Token payload contains:
```jsonc
{
  "sub": "<user_uuid>",
  "username": "alice",
  "access_level": 3,
  "role": "Risk Analyst",
  "exp": 1720000000
}
```

---

## 3. RAG Endpoints

### 3.1 Retrieve Top-K Chunks
| Method | Path             | Auth | Body (JSON)                                             | Response |
|--------|------------------|------|---------------------------------------------------------|----------|
| POST   | `/rag/retrieve`  | ✅    | `{ "query": "What is Basel III?", "session_id?": "uuid" }` | See below |

**Response Schema**
```jsonc
{
  "query": "What is Basel III?",
  "chunks": [
    {
      "chunk_id": "…",
      "document_type": "Regulatory Docs",
      "citation": "BDDK – Yönetici Özeti",
      "content": "<summary / relevant / full>…",
      "distance": 0.23
    }
  ]
}
```
*Returns at most 3 chunks* that the user is **allowed** to see according to the 5-level access matrix.
If no chunks match → 404. If user lacks permission → 403.

### 3.2 Generate Answer
| Method | Path          | Auth | Body (JSON)                                | Response |
|--------|---------------|------|--------------------------------------------|----------|
| POST   | `/rag/answer` | ✅    | `{ "query": "Explain LCR", "session_id?": "uuid" }` | `{ "query": "…", "answer": "…" }` |

– Builds context from same retrieval logic.  
– If all matched chunks are `summary`/`relevant` level the endpoint **returns them directly** (no LLM) to save tokens.  
– Otherwise runs Yi-1.5-9B-Chat (can be ~2-4 s).  
– `session_id` (optional) groups multiple Q&A into one conversation in history.

Error codes identical to `/rag/retrieve`.

---

## 4. Query History

All routes below require a valid Bearer token and return data **only for the current user**.

### 4.1 List Sessions
| Method | Path              | Auth | Body | Response |
|--------|-------------------|------|------|----------|
| GET    | `/history/sessions` | ✅ | — | `[{ "session_id": "uuid", "last_query": "text", "last_created_at": "ISO" }]` |

### 4.2 Get Messages in a Session
| Method | Path                                       | Auth | Response |
|--------|--------------------------------------------|------|----------|
| GET    | `/history/sessions/{session_id}`           | ✅   | `[{ "id": "…", "route": "answer", "query_text": "…", "response_text": "…", "created_at": "ISO" }, …]` |

### 4.3 Delete a Session
| Method | Path                             | Auth | Response |
|--------|----------------------------------|------|----------|
| DELETE | `/history/sessions/{session_id}` | ✅   | **204** No Content |

---

## 5. Interactive API Docs
* Swagger-UI: `GET /docs`  
* ReDoc: `GET /redoc`

Both are auto-generated and honor JWT auth (click "Authorize" → add token).

---

## 6. Request Examples (fetch)
```js
// Login
const res = await fetch("/auth/login", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ username: "alice", password: "secret" })
});
const { access_token } = await res.json();

// Retrieve
const chunksRes = await fetch("/rag/retrieve", {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
    "Authorization": `Bearer ${access_token}`
  },
  body: JSON.stringify({ query: "Basel III capital ratios" })
});

// Answer
const answerRes = await fetch("/rag/answer", {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
    "Authorization": `Bearer ${access_token}`
  },
  body: JSON.stringify({ query: "Summarize Basel III" })
});
```

---

## 7. Error Handling
| Code | Cause | Notes |
|------|-------|-------|
| 401  | Missing / invalid JWT | Login again or renew token |
| 403  | Access matrix denies requested info | Display "Insufficient permissions" |
| 404  | No documents / session not found | Show friendly fallback |
| 500  | Unexpected server error | Retry or contact admin |

---
