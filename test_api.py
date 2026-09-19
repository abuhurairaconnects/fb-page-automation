import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from fastapi.testclient import TestClient
from main import app
from config import settings

client = TestClient(app)

def test_endpoints():
    print("Testing API endpoints...")

    # 1. Health check
    res = client.get("/health")
    assert res.status_code == 200
    print("✓ /health passed:", res.json())

    # 2. Webhook verification GET (Meta challenge)
    verify_token = settings.VERIFY_TOKEN
    challenge = "1158201244"
    res = client.get(f"/webhook?hub.mode=subscribe&hub.verify_token={verify_token}&hub.challenge={challenge}")
    assert res.status_code == 200
    assert res.text == challenge
    print("✓ /webhook GET (Meta challenge verification) passed!")

    # 3. Webhook verification GET with wrong token
    res = client.get(f"/webhook?hub.mode=subscribe&hub.verify_token=wrong_token&hub.challenge={challenge}")
    assert res.status_code == 403
    print("✓ /webhook GET (Forbidden on wrong token) passed!")

    # 4. Webhook event intake POST (Messenger text)
    mock_messenger_payload = {
        "object": "page",
        "entry": [
            {
                "id": "100200300",
                "time": 1710000000,
                "messaging": [
                    {
                        "sender": {"id": "test_sender_456"},
                        "recipient": {"id": "100200300"},
                        "timestamp": 1710000000,
                        "message": {
                            "mid": "mid.test_message_123",
                            "text": "Hello, product details please"
                        }
                    }
                ]
            }
        ]
    }
    res = client.post("/webhook", json=mock_messenger_payload)
    assert res.status_code == 200
    assert res.text == "EVENT_RECEIVED"
    print("✓ /webhook POST (Messenger message intake) passed!")

    # 5. Webhook event intake POST (Comment on page post)
    mock_comment_payload = {
        "object": "page",
        "entry": [
            {
                "id": "100200300",
                "time": 1710000000,
                "changes": [
                    {
                        "field": "feed",
                        "value": {
                            "item": "comment",
                            "verb": "add",
                            "comment_id": "comment_998877",
                            "post_id": "post_112233",
                            "message": "Price koto?",
                            "from": {
                                "id": "commenter_user_777",
                                "name": "Abir Hasan"
                            }
                        }
                    }
                ]
            }
        ]
    }
    res = client.post("/webhook", json=mock_comment_payload)
    assert res.status_code == 200
    assert res.text == "EVENT_RECEIVED"
    print("✓ /webhook POST (Post comment intake) passed!")

    print("\n🎉 ALL API ENDPOINT TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    test_endpoints()
