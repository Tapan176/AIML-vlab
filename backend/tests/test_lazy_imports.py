"""Guard: building the Flask app must NOT import the heavy DL stack.

TensorFlow / Torch / Keras / Ultralytics each add seconds of cold-start and
hundreds of MB of RAM — on the free tier that's the difference between booting
and OOM. Every DL trainer is lazy-imported inside its route, so a fresh app
build must stay clean. A stray top-level `import torch` anywhere on the startup
path will fail this test.

Run in a fresh subprocess so the check is independent of whatever the rest of
the suite happened to import into this interpreter's sys.modules.
"""
import os
import subprocess
import sys

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

_PROBE = r"""
import os, sys
os.environ.setdefault('JWT_SECRET', 'lazy-import-test-secret-not-for-production')
os.environ.setdefault('SUBSCRIPTION_ENABLED', 'false')
import mongomock
from mongoDb import connection
connection.init_db(client_factory=mongomock.MongoClient)
from app import create_app
create_app(testing=True, init_database=False, run_migrations_on_start=False)
heavy = {'tensorflow', 'torch', 'keras', 'ultralytics', 'transformers'}
print('HEAVY:' + ','.join(sorted({m.split('.')[0] for m in sys.modules} & heavy)))
"""


def test_app_startup_does_not_import_heavy_libs():
    res = subprocess.run(
        [sys.executable, '-c', _PROBE],
        cwd=BACKEND, capture_output=True, text=True,
    )
    assert res.returncode == 0, f"probe failed:\n{res.stderr}"
    marker = next((l for l in res.stdout.splitlines() if l.startswith('HEAVY:')), None)
    assert marker is not None, f"probe produced no marker:\n{res.stdout}\n{res.stderr}"
    loaded = marker[len('HEAVY:'):].strip()
    assert loaded == '', f"heavy DL libs imported at app startup: {loaded}"
