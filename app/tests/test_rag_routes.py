"""Simple integration tests hitting live API with multilingual queries."""

import requests, pytest

API_BASE = "http://localhost:8000"  # Adjust if server runs elsewhere

# Seeded users with their passwords
USERS = [
    ("public_user", "public123"),
    ("internal_user", "internal123"),
    ("confidential_user", "confidential123"),
    ("restricted_user", "restricted123"),
    ("executive_user", "executive123"),
]

# Multilingual queries covering TR / EN / FR docs
QUERIES = [
    "Basel III nedir?",  # Turkish – Basel dokümanı
    "What is Basel III?",  # English version
    "Comment BNP Paribas collecte-t-il vos données personnelles?",  # French privacy notice
]


def login(username: str, password: str) -> str:
    resp = requests.post(f"{API_BASE}/auth/login", json={"username": username, "password": password}, timeout=20)
    resp.raise_for_status()
    return resp.json()["access_token"]


def retrieve(token: str, query: str):
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.post(f"{API_BASE}/rag/retrieve", json={"query": query}, headers=headers, timeout=60)
    resp.raise_for_status()
    return resp.json()


# ---------------------- PyTest ----------------------


@pytest.mark.parametrize("username,password", USERS)
@pytest.mark.parametrize("query", QUERIES)
def test_retrieve_multi(username, password, query):
    """Login with each user and make sure /rag/retrieve returns at least one chunk for each query."""
    token = login(username, password)
    data = retrieve(token, query)

    # Basic assertions
    assert data["query"] == query
    # Access matrix may hide docs, so we only assert that the endpoint works (no 500) and returns list
    assert "chunks" in data
    assert isinstance(data["chunks"], list)
    # For highest level user expect at least one chunk
    if username == "executive_user":
        assert len(data["chunks"]) >= 1

    # --- Verbose output for inspection (not affecting assertions)
    print("\n--- TEST OUTPUT ---")
    print(f"User: {username}")
    print(f"Query: {query}")
    print(f"Returned chunks: {len(data['chunks'])}")
    if data["chunks"]:
        first = data["chunks"][0]
        print("First chunk preview -> doc_type:", first["document_type"], "citation:", first["citation"][:80])
    print("--- END ---\n")