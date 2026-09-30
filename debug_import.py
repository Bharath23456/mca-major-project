import traceback
import sys

try:
    from fastapi.testclient import TestClient
    from app.main import app
    print('Imports OK')
except Exception:
    traceback.print_exc()
    sys.exit(1)

try:
    client = TestClient(app)
    print('TestClient OK')
except Exception:
    traceback.print_exc()
    sys.exit(1)

print('Debug script finished')
