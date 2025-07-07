import pytest, requests

API_BASE = "http://localhost:8000"

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
]


def login(username: str, password: str) -> str:
    resp = requests.post(f"{API_BASE}/auth/login", json={"username": username, "password": password}, timeout=20)
    resp.raise_for_status()
    return resp.json()["access_token"]


def answer(token: str, query: str):
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.post(f"{API_BASE}/rag/answer", json={"query": query}, headers=headers, timeout=300)
    resp.raise_for_status()
    return resp.json()


@pytest.mark.parametrize("username,password", USERS)
@pytest.mark.parametrize("query", QUERIES)
def test_answer_multi(username, password, query):
    token = login(username, password)
    data = answer(token, query)

    assert data["query"] == query
    assert "answer" in data
    assert isinstance(data["answer"], str) and len(data["answer"]) > 0

    # Verbose
    print("\n--- ANSWER OUTPUT ---")
    print(f"User: {username} | Query: {query}")
    print("Response (first 400 chars):", data["answer"][:400], "...\n") 