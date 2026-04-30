"""Generate L0/L1 tier files for a directory tree.

Usage:
    python generate_tiers.py <source_dir> [--output <context_dir>]

Walks the source directory, reads each file, and produces placeholder
L0 and L1 markdown files under .context/ (or the specified output dir).
The agent should review and refine the generated content.
"""

import argparse
import os
import sys
from pathlib import Path

SKIP_DIRS = {
    "node_modules", ".git", "build", "dist", "__pycache__",
    ".gradle", ".idea", ".vscode", ".cursor", ".context",
    "vendor", "venv", ".venv", "env", ".env", "target",
    ".next", ".nuxt", "coverage", ".cache",
}

SKIP_EXTENSIONS = {
    ".lock", ".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico",
    ".woff", ".woff2", ".ttf", ".eot", ".mp3", ".mp4", ".wav",
    ".zip", ".tar", ".gz", ".pdf", ".bin", ".exe", ".dll",
    ".so", ".dylib", ".class", ".jar", ".pyc", ".pyo",
    ".map", ".min.js", ".min.css",
}

SOURCE_EXTENSIONS = {
    ".py", ".js", ".ts", ".tsx", ".jsx", ".java", ".kt", ".kts",
    ".go", ".rs", ".rb", ".php", ".cs", ".cpp", ".c", ".h",
    ".swift", ".dart", ".vue", ".svelte",
    ".json", ".yaml", ".yml", ".toml", ".xml", ".gradle",
    ".md", ".sql", ".sh", ".bash", ".dockerfile",
}

MAX_FILE_SIZE = 100_000  # skip files larger than 100KB for auto-gen


def should_skip_dir(name: str) -> bool:
    return name.startswith(".") and name != ".context" or name in SKIP_DIRS


def should_process_file(path: Path) -> bool:
    if path.suffix.lower() in SKIP_EXTENSIONS:
        return False
    if path.suffix.lower() not in SOURCE_EXTENSIONS:
        return False
    if path.stat().st_size > MAX_FILE_SIZE:
        return False
    return True


def make_l0_placeholder(filepath: Path, relpath: str) -> str:
    return f"{filepath.name} - [TODO: one-sentence description]. Key exports: [TODO].\n"


def make_l1_placeholder(filepath: Path, relpath: str) -> str:
    return f"""# {filepath.name}

## Purpose
[TODO: 2-3 sentences on what this file does and why it exists]

## Key Exports / Entry Points
- [TODO: list main functions, classes, or constants]

## Dependencies
- [TODO: key imports]

## Relationships
- Called by: [TODO]
- Calls: [TODO]
"""


def make_dir_l0(dirpath: Path, file_count: int) -> str:
    return f"{dirpath.name}/ - [TODO: what this directory contains]. {file_count} files.\n"


def make_dir_l1(dirpath: Path, children: list[str]) -> str:
    listing = "\n".join(f"- `{c}`" for c in sorted(children)[:20])
    return f"""# {dirpath.name}/

## Purpose
[TODO: what this directory manages]

## Contents
{listing}

## Key Relationships
[TODO: how this directory relates to the rest of the project]
"""


def generate(source: Path, output: Path) -> dict:
    stats = {"dirs": 0, "files": 0, "skipped": 0}

    for root, dirs, files in os.walk(source):
        dirs[:] = [d for d in dirs if not should_skip_dir(d)]
        root_path = Path(root)
        rel = root_path.relative_to(source)

        ctx_dir = output / rel
        ctx_dir.mkdir(parents=True, exist_ok=True)

        processable = [f for f in files if should_process_file(root_path / f)]

        dir_l0 = ctx_dir / "_dir.l0.md"
        dir_l1 = ctx_dir / "_dir.l1.md"
        if not dir_l0.exists():
            dir_l0.write_text(make_dir_l0(root_path, len(processable)), encoding="utf-8")
        if not dir_l1.exists():
            dir_l1.write_text(make_dir_l1(root_path, processable), encoding="utf-8")
        stats["dirs"] += 1

        for fname in processable:
            fpath = root_path / fname
            frel = fpath.relative_to(source)

            l0_path = ctx_dir / f"{fname}.l0.md"
            l1_path = ctx_dir / f"{fname}.l1.md"

            if not l0_path.exists():
                l0_path.write_text(make_l0_placeholder(fpath, str(frel)), encoding="utf-8")
            if not l1_path.exists():
                l1_path.write_text(make_l1_placeholder(fpath, str(frel)), encoding="utf-8")
            stats["files"] += 1

    return stats


def main():
    parser = argparse.ArgumentParser(description="Generate L0/L1 context tiers")
    parser.add_argument("source", help="Source directory to index")
    parser.add_argument("--output", help="Output .context directory (default: <source>/.context)")
    args = parser.parse_args()

    source = Path(args.source).resolve()
    if not source.is_dir():
        print(f"Error: {source} is not a directory", file=sys.stderr)
        sys.exit(1)

    output = Path(args.output) if args.output else source / ".context"
    output.mkdir(parents=True, exist_ok=True)

    root_l0 = output / "_root.l0.md"
    root_l1 = output / "_root.l1.md"
    if not root_l0.exists():
        root_l0.write_text(
            f"{source.name} - [TODO: one-sentence project description].\n",
            encoding="utf-8",
        )
    if not root_l1.exists():
        root_l1.write_text(
            f"# {source.name}\n\n## Purpose\n[TODO]\n\n## Tech Stack\n[TODO]\n\n"
            f"## Directory Structure\n[TODO]\n\n## Entry Points\n[TODO]\n",
            encoding="utf-8",
        )

    stats = generate(source, output)
    print(f"Done: {stats['dirs']} directories, {stats['files']} files indexed to {output}")


if __name__ == "__main__":
    main()
