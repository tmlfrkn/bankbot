# Multilingual RAG Ingestion Pipeline – Technical Overview

File: `rag_pipeline_fixed.py`

This standalone script populates the **vector store** (`document_chunks` table) used by the BankBot backend. It is intended to be executed ad-hoc (or via CI) when new source documents need to be indexed.

---

## 1. Execution Flow

1. **Logging & ENV** – The script enables INFO logging and reads DB / model paths from environment variables (`DB_*`, `YI_MODEL_PATH`).
2. **DB Connection** – Connects to PostgreSQL via psycopg2.
3. **Schema Setup** – Runs `CREATE EXTENSION IF NOT EXISTS vector` and (re-)creates the `document_chunks` table with `VECTOR(1024)` embedding column + ivfflat index.
4. **Model Loading**
   * **Embeddings**: `SentenceTransformer('intfloat/multilingual-e5-large')` (GPU if available).
   * **LLM**: `Yi-1.5-9B-Chat` via `ctransformers` (quantised `.gguf`).
5. **Document Parsing** – Hard-coded content strings for 4 sample docs (TEB, BNP Paribas, Basel III, Bank of America). `parse_document()` splits them into *sections → sub-sections* and returns chunk dicts.
6. **Per-Chunk Processing**
   * Generate **summary** (`get_summary_from_yi`) – 5–7 sentence Turkish/English/ French summarisation prompt.
   * Generate **labels** (`get_labels_from_yi`) – 4 keyword tags.
   * Generate **embedding** – 1024-d float list.
   * Persist row via `INSERT INTO document_chunks (…) VALUES (…)`.
7. **Finish** – Closes DB connection and exits.

Total runtime ~3–4 min on laptop with GPU; produces ~150 chunks.

---

## 2. Table Definition
```sql
CREATE TABLE document_chunks (
    chunk_id        UUID PRIMARY KEY,
    source_document VARCHAR(255) NOT NULL,
    entity          VARCHAR(100),
    language        VARCHAR(5),
    document_type   VARCHAR(100) NOT NULL,
    main_section_title TEXT,
    sub_section_title  TEXT,
    text_content    TEXT NOT NULL,
    summary         TEXT,
    generated_labels TEXT[],
    embedding       VECTOR(1024)
);

CREATE INDEX document_chunks_embedding_idx
ON document_chunks USING ivfflat (embedding vector_l2_ops) WITH (lists = 100);
```

---

## 3. Extending the Pipeline

1. **Add new docs** – Import content (from PDF → text) and append to parsing section.
2. **Adjust dimensions** – If using a different embedding model, change `VECTOR(768)` etc.
3. **Swap LLM** – Replace `Yi-1.5` calls with OpenAI/Mistral; functions are isolated.
4. **Batch size** – For thousands of docs, refactor to process in batches and reuse DB cursor.

---

*Last updated:* {{date}} 