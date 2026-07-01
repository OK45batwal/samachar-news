#!/bin/bash
set -e
python -c "
import os, sys
os.environ.setdefault('PORT', '8000')
try:
    from backend.database import init_db
    import asyncio
    asyncio.run(init_db())
except Exception as e:
    print(f'Startup error: {e}', file=sys.stderr)
    sys.exit(1)
"
exec uvicorn backend.app:app --host 0.0.0.0 --port ${PORT:-8000}
