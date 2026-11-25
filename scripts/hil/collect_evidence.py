"""Build a digest inventory of explicitly selected, already captured artifacts."""
import argparse
import hashlib
import json
from pathlib import Path


def collect(root, paths):
    root = Path(root).resolve()
    result = []
    for name in paths:
        path = (root / name).resolve()
        if not path.is_relative_to(root) or not path.is_file():
            raise ValueError("artifact must be a file within the evidence directory")
        relative = path.relative_to(root).as_posix()
        if any(row["path"] == relative for row in result):
            raise ValueError("duplicate artifact")
        digest = hashlib.sha256()
        with path.open("rb") as stream:
            for block in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(block)
        result.append({"path": relative, "sha256": digest.hexdigest()})
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", required=True)
    p.add_argument("--output", required=True)
    p.add_argument("paths", nargs="+", help="explicit non-secret artifact paths relative to root")
    a = p.parse_args()
    result = collect(a.root, a.paths)
    with Path(a.output).open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2)


if __name__ == "__main__":
    main()
