import urllib.request
import json

def test_api_root():
    url = "http://127.0.0.1:8000/"
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req) as response:
        code = response.getcode()
        body = json.loads(response.read().decode())
        print(f"[HTTP GET /] Status Code: {code}")
        print(f"[HTTP GET /] Response Body: {json.dumps(body, indent=2)}")
        assert code == 200
        assert body["status"] == "online"

if __name__ == "__main__":
    test_api_root()
