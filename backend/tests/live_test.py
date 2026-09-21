import requests

BASE = "http://127.0.0.1:8001"

def run_tests():
    print("1. Testing GET /api/v1/health...")
    r = requests.get(f"{BASE}/api/v1/health")
    print("Status:", r.status_code, r.json())
    assert r.status_code == 200

    print("\n2. Testing GET / (Frontend root)...")
    r = requests.get(f"{BASE}/")
    print("Status:", r.status_code, "Content-Length:", len(r.text), "Has title:", "FAQ Assistant" in r.text)
    assert r.status_code == 200

    print("\n3. Testing GET /css/style.css...")
    r = requests.get(f"{BASE}/css/style.css")
    print("Status:", r.status_code, "CSS length:", len(r.text))
    assert r.status_code == 200

    print("\n4. Testing GET /js/app.js...")
    r = requests.get(f"{BASE}/js/app.js")
    print("Status:", r.status_code, "JS length:", len(r.text))
    assert r.status_code == 200

    print("\n5. Testing POST /api/v1/chat with exact question...")
    r = requests.post(f"{BASE}/api/v1/chat", json={"question": "What payment methods do you accept?"})
    print("Status:", r.status_code, r.json())
    assert r.status_code == 200
    assert r.json()["is_fallback"] is False

    print("\n6. Testing POST /api/v1/chat with rephrased question...")
    r = requests.post(f"{BASE}/api/v1/chat", json={"question": "Which methods can I use to pay?"})
    print("Status:", r.status_code, r.json())
    assert r.status_code == 200
    assert r.json()["is_fallback"] is False

    print("\n7. Testing POST /api/v1/chat with out-of-domain query...")
    r = requests.post(f"{BASE}/api/v1/chat", json={"question": "What is the weather in Tokyo today?"})
    print("Status:", r.status_code, r.json())
    assert r.status_code == 200
    assert r.json()["is_fallback"] is True

    print("\n8. Testing POST /api/v1/chat with empty query...")
    r = requests.post(f"{BASE}/api/v1/chat", json={"question": "   "})
    print("Status:", r.status_code, r.json())
    assert r.status_code in (400, 422)

    print("\n9. Testing POST /api/v1/chat with XSS payload...")
    r = requests.post(f"{BASE}/api/v1/chat", json={"question": "<script>alert('XSS')</script>"})
    print("Status:", r.status_code, r.json())
    assert r.status_code == 200

    print("\n10. Testing POST /api/v1/chat with oversized query...")
    r = requests.post(f"{BASE}/api/v1/chat", json={"question": "How do I pay? " * 100})
    print("Status:", r.status_code, r.json())
    assert r.status_code == 422

    print("\n=== ALL 10 LIVE SERVER INTEGRATION TESTS PASSED PERFECTLY ===")

if __name__ == "__main__":
    run_tests()
