import asyncio
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
ALEMBIC_INI = PROJECT_ROOT / "alembic.ini"


def run_migrations():
    subprocess.run(
        [
            sys.executable,
            "-m",
            "alembic",
            "-c",
            str(ALEMBIC_INI),
            "upgrade",
            "head",
        ],
        cwd=PROJECT_ROOT,
        check=True,
    )


async def run_migrations_async():
    await asyncio.to_thread(run_migrations)
