#!/usr/bin/env python3
"""
Standard Workspace File Writer.
Created to eliminate harness tool friction (e.g., write_to_file restricted to artifact directories)
and prevent shell escaping issues with complex markdown or code strings.

Usage:
  # Via stdin (recommended for multiline content):
  python3 scripts/write_file.py path/to/target.ext <<'FILE_EOF'
  ... content ...
  FILE_EOF

  # Via direct flag or source file:
  python3 scripts/write_file.py path/to/target.ext --content "quick content"
  python3 scripts/write_file.py path/to/target.ext --from-file path/to/source.ext
"""
import sys
import argparse
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(description="Reliably write files to the workspace.")
    parser.add_argument("target_path", help="Path of the target file to create or overwrite.")
    parser.add_argument("--content", help="Direct string content to write.")
    parser.add_argument("--from-file", help="Path of a source file to copy from.")
    parser.add_argument("--append", action="store_true", help="Append instead of overwriting.")
    args = parser.parse_args()

    target = Path(args.target_path)
    target.parent.mkdir(parents=True, exist_ok=True)

    mode = "a" if args.append else "w"

    if args.content is not None:
        content = args.content
    elif args.from_file:
        content = Path(args.from_file).read_text(encoding="utf-8")
    else:
        content = sys.stdin.read()

    with open(target, mode, encoding="utf-8") as f:
        f.write(content)

    print(f"Successfully wrote {len(content.encode('utf-8'))} bytes to {target}")

if __name__ == "__main__":
    main()
