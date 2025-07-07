import requests

API = "http://localhost:8000"
USERS = [
    ("public_user", "public123"),
    ("internal_user", "internal123"),
    ("confidential_user", "confidential123"),
    ("restricted_user", "restricted123"),
    ("executive_user", "executive123"),
]
QUERY = "Basel III nedir?"

def login(u, p):
    r = requests.post(f"{API}/auth/login",
                      json={"username": u, "password": p},
                      timeout=20)
    r.raise_for_status()
    return r.json()["access_token"]

def answer(tok):
    h = {"Authorization": f"Bearer {tok}"}
    r = requests.post(f"{API}/rag/answer",
                      json={"query": QUERY},
                      headers=h,
                      timeout=300)
    if r.status_code == 404:
        return f"[404] {r.json()['detail']}"
    r.raise_for_status()
    return r.json()["answer"]

if __name__ == "__main__":
    for u, p in USERS:
        print("\n###", u, "###")
        token = login(u, p)
        print("Login OK")
        print("Answer:")
        print(answer(token)[:600], "...\n")