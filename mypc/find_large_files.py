#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import shutil
import stat
import sys
from dataclasses import dataclass
from pathlib import Path


DEFAULT_EXCLUDES = {
    ".Trash",
    ".git",
    ".venv",
    "node_modules",
    "Library/Caches",
    "Library/Containers",
    "Library/Developer/CoreSimulator",
}


@dataclass
class FileEntry:
    path: Path
    size_bytes: int

    @property
    def size_mb(self) -> float:
        return self.size_bytes / (1024 * 1024)


def human_size(size_bytes: int) -> str:
    units = ["B", "KB", "MB", "GB", "TB"]
    size = float(size_bytes)
    for unit in units:
        if size < 1024 or unit == units[-1]:
            return f"{size:.1f}{unit}"
        size /= 1024
    return f"{size_bytes}B"


def is_excluded(path: Path, base: Path, excludes: set[str]) -> bool:
    try:
        rel = path.relative_to(base)
    except ValueError:
        return False
    rel_text = rel.as_posix()
    return any(rel_text == item or rel_text.startswith(f"{item}/") for item in excludes)


def walk_large_files(base: Path, min_size_bytes: int, excludes: set[str]) -> list[FileEntry]:
    results: list[FileEntry] = []

    for root, dirs, files in os.walk(base, topdown=True, followlinks=False):
        root_path = Path(root)
        dirs[:] = [
            d
            for d in dirs
            if not is_excluded(root_path / d, base, excludes)
        ]

        for filename in files:
            full_path = root_path / filename
            if is_excluded(full_path, base, excludes):
                continue
            try:
                file_stat = full_path.lstat()
            except (FileNotFoundError, PermissionError, OSError):
                continue
            if not stat.S_ISREG(file_stat.st_mode):
                continue
            if file_stat.st_size >= min_size_bytes:
                results.append(FileEntry(path=full_path, size_bytes=file_stat.st_size))

    results.sort(key=lambda item: item.size_bytes, reverse=True)
    return results


def print_results(entries: list[FileEntry], limit: int) -> None:
    if not entries:
        print("No files found above the selected size.")
        return

    print(f"Found {len(entries)} files:")
    for index, entry in enumerate(entries[:limit], start=1):
        print(f"{index:>3}. {human_size(entry.size_bytes):>8}  {entry.path}")

    if len(entries) > limit:
        print(f"... showing first {limit} of {len(entries)} results")


def unique_trash_destination(path: Path, trash_dir: Path) -> Path:
    candidate = trash_dir / path.name
    if not candidate.exists():
        return candidate

    stem = path.stem
    suffix = path.suffix
    counter = 1
    while True:
        candidate = trash_dir / f"{stem}-{counter}{suffix}"
        if not candidate.exists():
            return candidate
        counter += 1


def move_to_trash(entry: FileEntry) -> Path:
    trash_dir = Path.home() / ".Trash"
    trash_dir.mkdir(parents=True, exist_ok=True)
    destination = unique_trash_destination(entry.path, trash_dir)
    shutil.move(str(entry.path), str(destination))
    return destination


def prompt_for_selection(entries: list[FileEntry], limit: int) -> list[FileEntry]:
    visible_entries = entries[:limit]
    print()
    print("Enter numbers to move files to ~/.Trash (example: 1 3 7).")
    print("Press Enter to exit without moving anything.")
    raw = input("> ").strip()
    if not raw:
        return []

    selected: list[FileEntry] = []
    seen: set[int] = set()
    for part in raw.replace(",", " ").split():
        try:
            index = int(part)
        except ValueError:
            print(f"Skipping invalid value: {part}")
            continue
        if index < 1 or index > len(visible_entries):
            print(f"Skipping out-of-range value: {index}")
            continue
        if index in seen:
            continue
        seen.add(index)
        selected.append(visible_entries[index - 1])
    return selected


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Scan for large files and optionally move selected ones to ~/.Trash."
    )
    parser.add_argument(
        "path",
        nargs="?",
        default=str(Path.home()),
        help="Base path to scan. Defaults to your home directory.",
    )
    parser.add_argument(
        "--min-mb",
        type=int,
        default=100,
        help="Minimum file size in MB. Default: 100",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=200,
        help="Maximum number of results to display. Default: 200",
    )
    parser.add_argument(
        "--include-cache",
        action="store_true",
        help="Include common cache/container folders that are skipped by default.",
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Prompt to move selected files to ~/.Trash after listing results.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    base = Path(args.path).expanduser().resolve()

    if not base.exists():
        print(f"Path not found: {base}", file=sys.stderr)
        return 1
    if not base.is_dir():
        print(f"Path is not a directory: {base}", file=sys.stderr)
        return 1
    if args.min_mb <= 0:
        print("--min-mb must be greater than 0", file=sys.stderr)
        return 1
    if args.limit <= 0:
        print("--limit must be greater than 0", file=sys.stderr)
        return 1

    excludes = set() if args.include_cache else DEFAULT_EXCLUDES
    min_size_bytes = args.min_mb * 1024 * 1024
    entries = walk_large_files(base, min_size_bytes, excludes)
    print_results(entries, args.limit)

    if not args.interactive or not entries:
        return 0

    selected = prompt_for_selection(entries, args.limit)
    if not selected:
        print("No files moved.")
        return 0

    print()
    for entry in selected:
        try:
            destination = move_to_trash(entry)
            print(f"Moved to trash: {entry.path} -> {destination}")
        except Exception as exc:  # noqa: BLE001
            print(f"Failed to move {entry.path}: {exc}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
