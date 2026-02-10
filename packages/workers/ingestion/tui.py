#!/usr/bin/env python3
"""Simple TUI for testing the Bibliotalk Ingestion Worker API."""

from __future__ import annotations

import json
import sys

import httpx

BASE = "http://localhost:8000/api/v1/ingestion"
TIMEOUT = httpx.Timeout(120.0)


# -- helpers ----------------------------------------------------------------

def api(method: str, path: str, **kwargs) -> httpx.Response:
    url = f"{BASE}{path}"
    r = httpx.request(method, url, timeout=TIMEOUT, **kwargs)
    if r.status_code >= 400:
        print(f"\n  [ERROR {r.status_code}] {r.text}")
        sys.exit(1)
    return r


def heading(text: str) -> None:
    w = max(len(text) + 4, 50)
    print(f"\n{'━' * w}")
    print(f"  {text}")
    print(f"{'━' * w}\n")


def prompt(msg: str, default: str = "") -> str:
    suffix = f" [{default}]" if default else ""
    val = input(f"  {msg}{suffix}: ").strip()
    return val or default


# -- steps ------------------------------------------------------------------

def step_create() -> str:
    heading("1 · Create Session")
    name = prompt("Person's name")
    canon = prompt("Existing canon path (blank for new)", "")
    body: dict = {"name": name}
    if canon:
        body["canon_path"] = canon
    r = api("POST", "/sessions", json=body)
    session = r.json()
    sid = session["id"]
    print(f"\n  Session created: {sid}")
    return sid


def step_suggest(sid: str) -> list[dict]:
    heading("2 · Source Suggestions")
    print("  Asking AI for source suggestions …")
    r = api("GET", f"/sessions/{sid}/sources/suggest")
    suggestions = r.json()
    for i, s in enumerate(suggestions, 1):
        print(f"  {i}. [{s.get('type', '?'):>8}]  {s.get('url', '?')}")
        if s.get("label"):
            print(f"     {s['label']}")
    return suggestions


def step_sources(sid: str, suggestions: list[dict]) -> None:
    heading("3 · Confirm Sources")
    print("  Commands:")
    print("    a       – accept all suggestions")
    print("    1,3,5   – pick by number")
    print("    +url    – add a URL  (e.g. +https://example.com)")
    print("    u       – upload a local file")
    print("    d       – done\n")

    chosen: list[dict] = []
    while True:
        cmd = prompt(">>>", "a").lower()
        if cmd == "a":
            chosen = suggestions[:]
            print(f"  Accepted all {len(chosen)} suggestions.")
            break
        elif cmd == "d":
            break
        elif cmd == "u":
            path = prompt("File path")
            _upload_file(sid, path)
            continue
        elif cmd.startswith("+"):
            url = cmd[1:].strip()
            stype = prompt("Type (web/youtube/rss/file)", "web")
            label = prompt("Label (optional)", "")
            chosen.append({"type": stype, "url": url, "label": label})
            print(f"  Added: {url}")
        else:
            try:
                indices = [int(x.strip()) - 1 for x in cmd.split(",")]
                for idx in indices:
                    if 0 <= idx < len(suggestions):
                        chosen.append(suggestions[idx])
                        print(f"  Picked: {suggestions[idx].get('url')}")
            except ValueError:
                print("  Invalid input.")
                continue

    if chosen:
        api("POST", f"/sessions/{sid}/sources", json={"sources": chosen})
        print(f"\n  {len(chosen)} sources submitted.")


def _upload_file(sid: str, path: str) -> None:
    try:
        with open(path, "rb") as f:
            r = api(
                "POST",
                f"/sessions/{sid}/upload",
                files={"file": (path.rsplit("/", 1)[-1], f)},
            )
        src = r.json()
        print(f"  Uploaded → {src.get('label')} (type={src.get('type')})")
    except FileNotFoundError:
        print(f"  File not found: {path}")


def step_plan(sid: str) -> None:
    heading("4 · Generate Plan")
    print("  Generating ingestion plan …")
    r = api("GET", f"/sessions/{sid}/plan")
    plan = r.json().get("plan", "")
    print()
    for line in plan.splitlines():
        print(f"  {line}")
    print()

    while True:
        cmd = prompt("confirm / edit / regenerate", "confirm").lower()
        if cmd == "confirm":
            break
        elif cmd == "regenerate":
            print("  Regenerating …")
            r = api("GET", f"/sessions/{sid}/plan")
            plan = r.json().get("plan", "")
            for line in plan.splitlines():
                print(f"  {line}")
        elif cmd == "edit":
            print("  Enter replacement plan (end with a blank line):")
            lines: list[str] = []
            while True:
                line = input()
                if not line:
                    break
                lines.append(line)
            api("PATCH", f"/sessions/{sid}/plan", json={"plan": "\n".join(lines)})
            print("  Plan updated.")
            break


def step_execute(sid: str) -> None:
    heading("5 · Execute")
    print("  Confirming plan and starting execution …\n")
    api("POST", f"/sessions/{sid}/plan/confirm")

    # Stream SSE output.
    url = f"{BASE}/sessions/{sid}/execute/stream"
    try:
        with httpx.stream("GET", url, timeout=httpx.Timeout(600.0)) as resp:
            for line in resp.iter_lines():
                if line.startswith("data:"):
                    msg = line[5:].strip()
                    print(f"  {msg}")
                    if msg in ("[DONE]", "[ERROR]"):
                        break
    except httpx.ReadTimeout:
        print("  [stream timed out]")


def step_output(sid: str) -> None:
    heading("6 · Output")
    r = api("GET", f"/sessions/{sid}/output")
    files = r.json().get("files", [])
    if not files:
        print("  No output files.")
        return
    print(f"  {len(files)} files generated:\n")
    for f in files:
        size_kb = f["size"] / 1024
        print(f"    {f['filename']:<50} {size_kb:>6.1f} KB")


# -- main ------------------------------------------------------------------

def main() -> None:
    print("\n  ╔══════════════════════════════════════╗")
    print("  ║  Bibliotalk Ingestion Worker — TUI   ║")
    print("  ╚══════════════════════════════════════╝")

    try:
        httpx.get(f"{BASE}/sessions/nonexistent", timeout=3.0)
    except httpx.ConnectError:
        print(f"\n  Cannot connect to {BASE}")
        print("  Start the server first:")
        print("    cd packages/workers/ingestion")
        print("    pip install -e .")
        print("    python -m ingestion.main\n")
        sys.exit(1)

    sid = step_create()
    suggestions = step_suggest(sid)
    step_sources(sid, suggestions)
    step_plan(sid)
    step_execute(sid)
    step_output(sid)

    print("\n  Done.\n")


if __name__ == "__main__":
    main()
