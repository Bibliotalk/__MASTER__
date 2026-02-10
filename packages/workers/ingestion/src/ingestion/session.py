from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from .config import settings
from .models import CanonIndex, Session


class SessionStore:
    """File-backed session persistence."""

    @property
    def _dir(self) -> Path:
        d = settings.data_dir / "sessions"
        d.mkdir(parents=True, exist_ok=True)
        return d

    def _path(self, session_id: str) -> Path:
        return self._dir / f"{session_id}.json"

    # -- CRUD ---------------------------------------------------------------

    def create(self, session: Session) -> Session:
        # If a canon_path was supplied, pre-load the existing index for dedup.
        if session.canon_path:
            idx_path = Path(session.canon_path) / "index.json"
            if idx_path.exists():
                session.existing_index = CanonIndex.model_validate_json(
                    idx_path.read_text()
                )
        self._write(session)
        return session

    def get(self, session_id: str) -> Session | None:
        p = self._path(session_id)
        if not p.exists():
            return None
        return Session.model_validate_json(p.read_text())

    def update(self, session: Session) -> Session:
        session.updated_at = datetime.now(timezone.utc)
        self._write(session)
        return session

    def list_all(self) -> list[Session]:
        return [
            Session.model_validate_json(p.read_text())
            for p in sorted(self._dir.glob("*.json"))
        ]

    def delete(self, session_id: str) -> bool:
        p = self._path(session_id)
        if p.exists():
            p.unlink()
            return True
        return False

    # -- helpers ------------------------------------------------------------

    def _write(self, session: Session) -> None:
        self._path(session.id).write_text(
            session.model_dump_json(indent=2)
        )


store = SessionStore()
