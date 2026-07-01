#!/bin/bash
set -e
PORT=${PORT:-8000}
echo "Starting on port $PORT"
echo "DB URL: ${DATABASE_URL:0:30}..."
python -c "
import sys
import traceback
try:
    from backend.database import init_db
    import asyncio
    asyncio.run(init_db())
    print('DB init OK')
except Exception:
    print(f'FATAL: DB init failed', file=sys.stderr)
    traceback.print_exc(file=sys.stderr)
    sys.exit(1)
" 2>&1
exec uvicorn backend.app:app --host 0.0.0.0 --port $PORT --log-level trace 2>&1
