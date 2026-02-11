from __future__ import annotations

from .models import Job


class JobStore:
    """Simple in-memory dict-backed job store."""

    def __init__(self) -> None:
        self._jobs: dict[str, Job] = {}

    def create(self, job: Job) -> Job:
        self._jobs[job.id] = job
        return job

    def get(self, job_id: str) -> Job | None:
        return self._jobs.get(job_id)

    def update(self, job: Job) -> Job:
        self._jobs[job.id] = job
        return job


jobs = JobStore()
