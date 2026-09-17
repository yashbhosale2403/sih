import os
import sys
import urllib.request
import json

# Add workspace directory to python path
sys.path.insert(0, os.path.abspath('.'))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'securedocs.settings')
import django
django.setup()

from accounts.models import User, UserRole

def create_demo_user():
    username = "test_admin"
    password = "AdminPassword123!"
    badge_id = "BADGE-ADMIN-001"

    user, created = User.objects.get_or_create(
        username=username,
        defaults={
            "badge_id": badge_id,
            "role": UserRole.ADMIN,
            "is_staff": True,
            "is_superuser": True,
        }
    )
    user.set_password(password)
    user.save()
    print(f"[DB] Demo admin user '{username}' created/updated successfully.")
    return username, password

def test_jwt_login(username, password):
    url = "http://127.0.0.1:8000/api/auth/login/"
    payload = json.dumps({"username": username, "password": password}).encode('utf-8')
    req = urllib.request.Request(url, data=payload, headers={'Content-Type': 'application/json'})

    with urllib.request.urlopen(req) as response:
        code = response.getcode()
        data = json.loads(response.read().decode())
        print(f"[POST /api/auth/login/] Status Code: {code}")
        print(f"[POST /api/auth/login/] Access Token: {data['access'][:35]}...")
        print(f"[POST /api/auth/login/] Refresh Token: {data['refresh'][:35]}...")
        assert code == 200
        assert "access" in data
        assert "refresh" in data

if __name__ == "__main__":
    u, p = create_demo_user()
    test_jwt_login(u, p)
