"""Supabase (Postgres) keep-alive heartbeat.

Performs a single READ-ONLY query against the existing database so that the
Supabase project registers "user database activity" and does not hit the
free-tier 7-day auto-pause. It never inserts, updates, or deletes anything.

This repo talks to Supabase directly over Postgres (SQLAlchemy / psycopg2 in
utils/database.py), not through the Supabase REST API, so there is no
anon/publishable key involved. Connection details are read from environment
variables (supplied as GitHub Actions secrets) using the exact same names the
Streamlit app already uses: DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD.
"""

import os
import sys

import psycopg2

REQUIRED_VARS = ["DB_HOST", "DB_PORT", "DB_NAME", "DB_USER", "DB_PASSWORD"]


def main() -> int:
    missing = [var for var in REQUIRED_VARS if not os.environ.get(var)]
    if missing:
        print(
            f"Missing required environment variables: {', '.join(missing)}",
            file=sys.stderr,
        )
        return 1

    conn = None
    try:
        conn = psycopg2.connect(
            host=os.environ["DB_HOST"],
            port=os.environ["DB_PORT"],
            dbname=os.environ["DB_NAME"],
            user=os.environ["DB_USER"],
            password=os.environ["DB_PASSWORD"],
            sslmode="require",  # Supabase requires TLS
            connect_timeout=10,
        )
        with conn.cursor() as cur:
            # READ-ONLY: touch an existing lightweight catalog table so the
            # query counts as genuine database activity. No rows are modified.
            cur.execute("SELECT 1 FROM public.product LIMIT 1;")
            rows = cur.fetchall()
        print(f"Heartbeat read succeeded. Rows returned: {len(rows)}")
        return 0
    except Exception as exc:  # fail loudly so the Actions run shows red
        print(f"Heartbeat read failed: {exc}", file=sys.stderr)
        return 1
    finally:
        if conn is not None:
            conn.close()


if __name__ == "__main__":
    sys.exit(main())
