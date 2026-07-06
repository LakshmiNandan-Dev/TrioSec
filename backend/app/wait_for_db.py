"""Block until the database accepts connections (used by the container entrypoint)."""
import sys
import time

from sqlalchemy import text

from app.db import engine

DEADLINE = time.monotonic() + 120

while True:
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("database is ready")
        break
    except Exception as exc:  # noqa: BLE001
        if time.monotonic() > DEADLINE:
            print(f"database never became ready: {exc}", file=sys.stderr)
            sys.exit(1)
        time.sleep(2)
