#!/usr/bin/env python3
"""Generate a repository activity dashboard from tracked files and Git history."""

from __future__ import annotations

import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote


ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "dashboard" / "index.md"
TEXT_SUFFIXES = {
    ".c",
    ".cpp",
    ".csv",
    ".ino",
    ".ipynb",
    ".jl",
    ".m",
    ".md",
    ".py",
    ".r",
    ".txt",
}

CATEGORIES = [
    (
        "PID experiments",
        re.compile(r"\bpid\b|\bproportional\b|\bintegral\b|\bderivative\b|tuning", re.I),
    ),
    (
        "System analysis",
        re.compile(
            r"system analysis|transfer function|state.space|system model|"
            r"frequency response|time response",
            re.I,
        ),
    ),
    (
        "Stability studies",
        re.compile(
            r"\bstability\b|stable|unstable|routh|root locus|gain margin|"
            r"phase margin|nyquist",
            re.I,
        ),
    ),
    (
        "Control simulations",
        re.compile(
            r"\bsimulation\b|\bsimulate\b|control\.?system|step response|"
            r"closed.loop|open.loop|servo|motor control",
            re.I,
        ),
    ),
]


def git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return result.stdout


def tracked_paths() -> list[Path]:
    paths = git("ls-files", "-z").split("\0")
    return [
        Path(path)
        for path in paths
        if path
        and not path.startswith("dashboard/")
        and Path(path).as_posix().lower() != "readme.md"
        and Path(path).suffix.lower() in TEXT_SUFFIXES
    ]


def readable_text(path: Path) -> str:
    try:
        content = (ROOT / path).read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        print(f"Skipping unreadable tracked file {path}: {error}")
        return ""

    if path.suffix.lower() != ".ipynb":
        return content

    try:
        notebook = json.loads(content)
    except json.JSONDecodeError as error:
        print(f"Skipping invalid notebook {path}: {error}")
        return content

    cell_text = []
    for cell in notebook.get("cells", []):
        source = cell.get("source", [])
        cell_text.append("".join(source) if isinstance(source, list) else str(source))
    return "\n".join(cell_text)


def matching_files(paths: list[Path]) -> dict[str, list[str]]:
    found = {name: [] for name, _ in CATEGORIES}
    for path in paths:
        evidence = f"{path.as_posix()}\n{readable_text(path)}"
        for name, pattern in CATEGORIES:
            if pattern.search(evidence):
                found[name].append(path.as_posix())
    return found


def recent_commits() -> list[tuple[str, str, str]]:
    output = git("log", "-5", "--date=short", "--pretty=format:%h%x1f%ad%x1f%s")
    commits = []
    for line in output.splitlines():
        parts = line.split("\x1f", maxsplit=2)
        if len(parts) == 3:
            commits.append((parts[0], parts[1], parts[2]))
    return commits


def render() -> str:
    paths = tracked_paths()
    topics = matching_files(paths)
    covered = sum(bool(files) for files in topics.values())
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    lines = [
        "# Control Systems Engineering Dashboard",
        "",
        f"_Generated {generated_at} from tracked repository files and Git history._",
        "",
        "## Progress overview",
        "",
        (
            f"**Activity coverage: {covered}/{len(topics)} topics have repository "
            "evidence.** This measures discoverable artifacts, not experiment "
            "completion or engineering quality."
        ),
        "",
        "| Workstream | Evidence files | Status |",
        "| --- | ---: | --- |",
    ]
    for name, files in topics.items():
        status = "Evidence found" if files else "No evidence detected"
        lines.append(f"| {name} | {len(files)} | {status} |")

    for name, files in topics.items():
        lines.extend(["", f"## {name}", ""])
        if not files:
            lines.append("No matching tracked files detected yet.")
            continue
        for file_path in files:
            link = quote(file_path, safe="/")
            lines.append(f"- [{file_path}]({link})")

    lines.extend(["", "## Recent repository activity", ""])
    commits = recent_commits()
    if commits:
        for commit, date, subject in commits:
            lines.append(f"- `{date}` [`{commit}`](../commit/{commit}) - {subject}")
    else:
        lines.append("No commits are available in the local Git history.")

    lines.extend(
        [
            "",
            "---",
            "",
            "Updated automatically each day by "
            "[the dashboard workflow](../.github/workflows/dashboard.yml).",
            "",
        ]
    )
    return "\n".join(lines)


if __name__ == "__main__":
    OUTPUT.write_text(render(), encoding="utf-8")
    print(f"Generated {OUTPUT.relative_to(ROOT)}")
