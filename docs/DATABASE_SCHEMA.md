# BankBot Database Schema (PostgreSQL / SQLAlchemy)

This document lists the **core tables** currently used by the application. Optional or legacy tables have been omitted for brevity.

---

## 1. users
Stores login credentials and access-matrix level.
```sql
CREATE TABLE users (
    id            UUID PRIMARY KEY,
    username      VARCHAR(50) UNIQUE NOT NULL,
    email         VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    access_level  INT  NOT NULL, -- 1=Public … 5=Executive
    role          VARCHAR(50),
    is_active     BOOLEAN DEFAULT TRUE,
    is_admin      BOOLEAN DEFAULT FALSE,
    created_at    TIMESTAMPTZ DEFAULT NOW(),
    updated_at    TIMESTAMPTZ
);
```

---

## 2. document_chunks
Vector store for RAG retrieval – populated by the ingestion pipeline.
```sql
CREATE TABLE document_chunks (
    chunk_id          UUID PRIMARY KEY,
    source_document   VARCHAR(255) NOT NULL,
    entity            VARCHAR(100),
    language          VARCHAR(5),
    document_type     VARCHAR(100) NOT NULL,
    main_section_title TEXT,
    sub_section_title  TEXT,
    text_content      TEXT NOT NULL,
    summary           TEXT,
    embedding         VECTOR(1024)
);

CREATE INDEX document_chunks_embedding_idx
    ON document_chunks USING ivfflat (embedding vector_l2_ops) WITH (lists = 100);
```

---

## 3. query_history
Stores every `/rag/retrieve` and `/rag/answer` call for audit & UX.
```sql
CREATE TABLE query_history (
    id          UUID PRIMARY KEY,
    user_id     UUID NOT NULL REFERENCES users(id),
    session_id  UUID NOT NULL,
    route       VARCHAR(20) NOT NULL,  -- retrieve | answer
    query_text  TEXT NOT NULL,
    response_text TEXT,
    ip_address  VARCHAR(45),
    created_at  TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX query_hist_user_idx ON query_history(user_id);
CREATE INDEX query_hist_session_idx ON query_history(session_id);
```

---

## 4. audit_logs (optional)
Used for extended compliance logging (actions beyond RAG).

```sql
CREATE TABLE audit_logs (
    id          UUID PRIMARY KEY,
    user_id     UUID REFERENCES users(id),
    action      VARCHAR(50) NOT NULL,
    resource_type VARCHAR(50),
    resource_id   VARCHAR(255),
    user_access_level INT,
    document_type     VARCHAR(50),
    access_type_granted VARCHAR(20),
    query_text  TEXT,
    ip_address  VARCHAR(45),
    status_code INT,
    timestamp   TIMESTAMPTZ DEFAULT NOW()
);
```

---

## Relationships
```
users 1 ──► * query_history
users 1 ──► * audit_logs
```

---

*Last updated:* {{date}} 