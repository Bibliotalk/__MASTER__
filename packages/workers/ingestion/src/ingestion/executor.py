from __future__ import annotations

import asyncio
import sys
import tempfile
from pathlib import Path

from .config import settings
from .models import SessionStage
from .session import store

# Active execution streams: session_id → asyncio.Queue of log lines.
_streams: dict[str, asyncio.Queue[str | None]] = {}


def get_stream(session_id: str) -> asyncio.Queue[str | None] | None:
    return _streams.get(session_id)


async def execute(session_id: str, program: str) -> None:
    """Run *program* in a subprocess and stream output to the session log."""
    queue: asyncio.Queue[str | None] = asyncio.Queue()
    _streams[session_id] = queue

    # Resolve the package source root so the subprocess can import `ingestion.*`.
    src_root = str(Path(__file__).resolve().parent.parent)  # …/src

    try:
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False, dir=settings.data_dir
        ) as tmp:
            tmp.write(program)
            script_path = tmp.name

        env_pythonpath = f"{src_root}"
        proc = await asyncio.create_subprocess_exec(
            sys.executable,
            script_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            env={
                **dict(__import__("os").environ),
                "PYTHONPATH": env_pythonpath,
            },
        )

        assert proc.stdout is not None
        async for raw_line in proc.stdout:
            line = raw_line.decode("utf-8", errors="replace").rstrip()
            # Persist to session log.
            session = store.get(session_id)
            if session:
                session.log.append(line)
                store.update(session)
            await queue.put(line)

        await proc.wait()

        # Mark session as DONE or ERROR.
        session = store.get(session_id)
        if session:
            if proc.returncode == 0:
                session.stage = SessionStage.DONE
                await queue.put("[DONE]")
            else:
                session.stage = SessionStage.ERROR
                session.log.append(f"[exit code {proc.returncode}]")
                await queue.put(f"[ERROR] exit code {proc.returncode}")
            store.update(session)

    except Exception as exc:
        session = store.get(session_id)
        if session:
            session.stage = SessionStage.ERROR
            session.log.append(f"[executor error] {exc}")
            store.update(session)
        await queue.put(f"[ERROR] {exc}")
    finally:
        await queue.put(None)  # sentinel — signals end of stream
        # Clean up after consumers have had a chance to drain.
        _streams.pop(session_id, None)
        try:
            Path(script_path).unlink(missing_ok=True)
        except Exception:
            pass
