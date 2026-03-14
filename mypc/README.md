# Large file finder

Scans a directory for files above a size threshold and lists them from largest to smallest.

Examples:

```bash
python3 find_large_files.py
python3 find_large_files.py ~/Downloads --min-mb 100
python3 find_large_files.py ~ --min-mb 250 --limit 100 --interactive
```

Notes:

- By default it skips common noise folders such as `.Trash`, `.git`, `node_modules`, and some macOS cache/simulator folders.
- `--interactive` does not permanently delete files. It moves selected files to `~/.Trash`.
- Add `--include-cache` if you also want to inspect cache-heavy locations.
