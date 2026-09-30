import sys
import traceback

try:
    import pytest
except Exception:
    traceback.print_exc()
    sys.exit(1)

try:
    res = pytest.main(['-q', 'tests/test_app.py'])
    print('pytest exit code:', res)
except Exception:
    traceback.print_exc()
    sys.exit(1)
