#!/usr/bin/env python3
"""Quick manual demo: RAG /retrieve endpoint for 5 queries × 5 users.
Prints number of accessible chunks and first citation preview.
Run while FastAPI server is running.
"""
import requests

API = "http://localhost:8000"
USERS = [
    ("public_user", "public123"),
    ("internal_user", "internal123"),
    ("confidential_user", "confidential123"),
    ("restricted_user", "restricted123"),
    ("executive_user", "executive123"),
]

QUERIES = [
    "Basel III nedir?",
    "What is Basel III?",
    "Comment BNP Paribas collecte-t-il vos données personnelles?",
    "Müşterinin 5000 dolarlık yetkisiz işlemi itiraz etmesi durumunda yükseltme süreci nedir?",
    "How is customer data handled under GDPR?",
]

def login(username: str, password: str) -> str:
    resp = requests.post(f"{API}/auth/login", json={"username": username, "password": password}, timeout=20)
    resp.raise_for_status()
    return resp.json()["access_token"]

def retrieve(token: str, query: str):
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.post(f"{API}/rag/retrieve", json={"query": query}, headers=headers, timeout=60)
    if resp.status_code != 200:
        return None, resp.status_code, resp.text
    return resp.json(), 200, ""

if __name__ == "__main__":
    for user, pwd in USERS:
        print("=" * 140)
        print(f"USER: {user}")
        token = login(user, pwd)
        for q in QUERIES:
            data, code, err = retrieve(token, q)
            if code != 200:
                print(f"  Query: '{q}' -> HTTP {code}: {err[:120]}")
                continue
            chunks = data.get("chunks", [])
            print(f"  Query: '{q[:70]}...'  | total chunks: {len(chunks)}")
            for i, ch in enumerate(chunks, 1):
                preview = ch['content'][:120].replace("\n", " ")
                print(f"    [{i}] doc_type={ch['document_type']:<18} dist={ch['distance']:.4f} citation={ch['citation'][:60]}")
                print(f"        preview: {preview}...")
            if not chunks:
                print("    <no accessible chunks>") 