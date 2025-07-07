## Hierarchical Chunking Strategy in `rag_pipeline_fixed.py`

> **Purpose**: Convert long, structured banking / regulatory documents into coherent, self-contained *chunks* that can be embedded, indexed and later served selectively according to the Access Matrix.

---

### 1. Parsing Flow

1. **Document-level metadata** (source file, entity, language, document_type) is passed to `parse_document()`.
2. **Main sections** are detected by `## ` (two hash signs + space).
3. Inside each main section, the part **before the first `### `** is treated as the **introduction** of that section.
4. **Sub-sections** are detected by `### ` (three hash signs + space).

Illustration:
```
## 1. Basel III Nedir?
Intro para...
### a- Özkaynaklar
Body…
### b- Sermayeye İlişkin Oranlar
Body…
```

* `1. Basel III Nedir?` is a **main section title**.
* Text between the title and the first `###` is the **main intro**.
* Each `###` header starts a **sub-section**.

---

### 2. Chunk Types Created

| Chunk Scope | Stored Titles | Sub-section title field | Example Citation |
|-------------|--------------|-------------------------|------------------|
| **Main section intro** | `main_section_title = "1. Basel III Nedir?"` | `"Genel Açıklama"` | `BDDK – 1. Basel III Nedir?, Genel Açıklama` |
| **Sub-section** | Same as parent main section | Actual `###` header | `BDDK – 1. Basel III Nedir?, a- Özkaynaklar` |

> The citation string shown to users is built from `entity`, `main_section_title`, and `sub_section_title` (if any).

---

### 3. Chunk JSON Structure (simplified)
```json
{
  "chunk_id": "<uuid>",
  "source_document": "Sorularla_Basel_III_BDDK_Aralik_2010.pdf",
  "entity": "BDDK",
  "language": "tr",
  "document_type": "Regulatory Docs",
  "main_section_title": "1. Basel III Nedir?",
  "sub_section_title": "Genel Açıklama" | "a- Özkaynaklar" | ...,
  "text_content": "<raw text of this chunk>",
  "summary": "<Yi-generated summary>",
  "generated_labels": ["bankacılık", "sermaye", "düzenleme", "likidite"],
  "embedding": [1024-dim vector]
}
```

---

### 4. End-to-End Example
Given the excerpt above, two chunks are produced:

1. **Main Intro Chunk**
   * `sub_section_title = "Genel Açıklama"`
   * Citation → `BDDK – 1. Basel III Nedir?, Genel Açıklama`
2. **Sub-section Chunk** (`a- Özkaynaklar`)
   * `sub_section_title = "a- Özkaynaklar"`
   * Citation → `BDDK – 1. Basel III Nedir?, a- Özkaynaklar`

A sample retrieval response element becomes:
```json
{
  "chunk_id": "caeb20ee-5808-4c4f-ad5a-fe327d6ddad3",
  "citation": "BDDK – 1. Basel III Nedir?, Genel Açıklama",
  "content": "Dünyanın yüzleştiği en büyük finansal krizlerden biri... (truncated)",
  "distance": 0.6247,
  "document_type": "Regulatory Docs"
}
```

---

### 5. Rationale
* **Hierarchical split** mirrors the document outline, improving answer explainability and allowing fine-grained citations.
* Keeping **intro vs. detail** separate lets low-access users read only high-level summaries while executives can reach full text.
* Small chunk size (~1-3 paragraphs) balances semantic completeness and embedding recall.

---

### 6. Future Enhancements
1. Dynamic windowed chunking with overlap for very long sub-sections.
2. Support deeper heading levels (`####`) for extremely structured docs.
3. Store estimated token count per chunk to help prompt budgeting. 