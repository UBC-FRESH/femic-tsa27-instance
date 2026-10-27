#!/usr/bin/env python3
"""Verify the public-data manifest against the local mirror and instance paths.

The manifest is ``metadata/data_manifest.yaml``. Each entry is either ``available`` (the
script checks the path or the TSR corpus count) or ``to_fetch`` (the script reports it as
pending and does not fail the run). ``--write-lock`` records the digest, size, and file count
of every available entry in ``metadata/data_manifest.lock.yaml``.

Command-line usage::

    python scripts/verify_public_data.py
    python scripts/verify_public_data.py --write-lock
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

ROOT: Path = Path(__file__).resolve().parent.parent
DEFAULT_MANIFEST: Path = ROOT / "metadata" / "data_manifest.yaml"
DEFAULT_LOCK: Path = ROOT / "metadata" / "data_manifest.lock.yaml"
CHUNK_SIZE: int = 1024 * 1024


@dataclass(frozen=True)
class Result:
    """One verification result.

    Attributes
    ----------
    entry_id : str
        Manifest entry identifier.
    status : str
        ``present``, ``pending``, ``missing``, or ``mismatch``.
    detail : str
        Human-readable detail, including the resolved path or count.
    digest : str
        SHA-256 for a file, or a file-list digest for a directory. Empty when unavailable.
    size_bytes : int
        Total size in bytes, or 0 when unavailable.
    file_count : int
        Number of files in a directory or corpus, or 1 for a single file.
    """

    entry_id: str
    status: str
    detail: str
    digest: str = ""
    size_bytes: int = 0
    file_count: int = 0


def load_manifest(path: Path) -> dict[str, Any]:
    """Load and minimally validate the YAML manifest.

    Parameters
    ----------
    path : Path
        Manifest path.

    Returns
    -------
    dict of str to Any
        Parsed manifest.

    Raises
    ------
    ValueError
        When the manifest has no ``entries`` list.
    """
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or not isinstance(payload.get("entries"), list):
        raise ValueError(f"{path} has no entries list")
    return payload


def resolve_path(
    entry: dict[str, Any], instance_root: Path, external_root: Path | None
) -> Path | None:
    """Resolve an entry to the mirror path or the instance-local path.

    Parameters
    ----------
    entry : dict of str to Any
        One manifest entry.
    instance_root : Path
        Instance repository root.
    external_root : Path or None
        ``FEMIC_EXTERNAL_DATA_ROOT`` value, when set.

    Returns
    -------
    Path or None
        The resolved path, or None when the entry has no path.
    """
    mirror = entry.get("mirror_path")
    local = entry.get("local_path")
    if external_root is not None and mirror:
        candidate = external_root / str(mirror)
        if candidate.exists():
            return candidate
    if local:
        return instance_root / str(local)
    return None


def digest_path(path: Path) -> tuple[str, int, int]:
    """Return a digest, size, and file count for a file or directory.

    Parameters
    ----------
    path : Path
        File or directory.

    Returns
    -------
    tuple of (str, int, int)
        SHA-256 for a file; for a directory, a SHA-256 over the sorted
        ``relative_path:size`` lines. The size is the sum of file sizes and the count is
        the number of files.

    Raises
    ------
    FileNotFoundError
        When the path does not exist.
    """
    if not path.exists():
        raise FileNotFoundError(path)
    if path.is_file():
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            while chunk := handle.read(CHUNK_SIZE):
                digest.update(chunk)
        return digest.hexdigest(), path.stat().st_size, 1
    lines: list[str] = []
    total = 0
    count = 0
    for child in sorted(item for item in path.rglob("*") if item.is_file()):
        size = child.stat().st_size
        lines.append(f"{child.relative_to(path).as_posix()}:{size}")
        total += size
        count += 1
    digest = hashlib.sha256("\n".join(lines).encode("utf-8"))
    return digest.hexdigest(), total, count


def count_corpus_documents(path: Path) -> int:
    """Count the TSR PDFs under a corpus directory.

    Parameters
    ----------
    path : Path
        Corpus TSA directory.

    Returns
    -------
    int
        Number of ``*.pdf`` files.
    """
    return len(list(path.rglob("*.pdf"))) if path.exists() else 0


def display_path(path: Path, instance_root: Path, external_root: Path | None) -> str:
    """Return a portable path label for a verification result.

    Parameters
    ----------
    path : Path
        Resolved path.
    instance_root : Path
        Instance repository root.
    external_root : Path or None
        External data root, when set.

    Returns
    -------
    str
        ``mirror:<relative>``, ``local:<relative>``, or the file name.
    """
    for root, label in ((external_root, "mirror"), (instance_root, "local")):
        if root is None:
            continue
        try:
            return f"{label}:{path.relative_to(root).as_posix()}"
        except ValueError:
            continue
    return path.name


def verify_entry(entry: dict[str, Any], instance_root: Path, external_root: Path | None) -> Result:
    """Verify one manifest entry.

    Parameters
    ----------
    entry : dict of str to Any
        Manifest entry.
    instance_root : Path
        Instance repository root.
    external_root : Path or None
        ``FEMIC_EXTERNAL_DATA_ROOT`` value, when set.

    Returns
    -------
    Result
        The verification result.
    """
    entry_id = str(entry.get("id", "unknown"))
    if str(entry.get("status")) == "to_fetch":
        return Result(entry_id, "pending", "to_fetch; see fetch_command or note")
    path = resolve_path(entry, instance_root, external_root)
    if path is None:
        return Result(entry_id, "missing", "no local_path or mirror_path")
    if not path.exists():
        return Result(
            entry_id, "missing", f"not found: {display_path(path, instance_root, external_root)}"
        )
    if entry.get("check") == "tsr_corpus":
        expected = int(entry.get("expected_count", 0))
        count = count_corpus_documents(path)
        if count != expected:
            return Result(entry_id, "mismatch", f"{count} PDFs, expected {expected}")
        return Result(entry_id, "present", f"{count} PDFs", file_count=count)
    digest, size, count = digest_path(path)
    return Result(
        entry_id,
        "present",
        display_path(path, instance_root, external_root),
        digest,
        size,
        count,
    )


def write_lock(results: Sequence[Result], path: Path) -> None:
    """Write the verification lock file.

    Parameters
    ----------
    results : sequence of Result
        Verification results.
    path : Path
        Destination YAML path.
    """
    payload = {
        "generated_utc": datetime.now(UTC).isoformat(),
        "entries": {
            result.entry_id: {
                "status": result.status,
                "detail": result.detail,
                "sha256": result.digest,
                "size_bytes": result.size_bytes,
                "file_count": result.file_count,
            }
            for result in results
        },
    }
    path.write_text(yaml.safe_dump(payload, sort_keys=True), encoding="utf-8")


def main(argv: Sequence[str] | None = None) -> int:
    """Run the verification from the command line.

    Parameters
    ----------
    argv : sequence of str or None, optional
        Command-line arguments.

    Returns
    -------
    int
        ``0`` when every available entry is present and no entry is missing or mismatched,
        ``1`` otherwise.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--lock", type=Path, default=DEFAULT_LOCK)
    parser.add_argument("--write-lock", action="store_true")
    parser.add_argument("--json", action="store_true", help="Emit the results as JSON.")
    args = parser.parse_args(argv)
    manifest = load_manifest(args.manifest)
    value = os.environ.get("FEMIC_EXTERNAL_DATA_ROOT")
    external = Path(value) if value else None
    results = [verify_entry(entry, ROOT, external) for entry in manifest["entries"]]
    if args.write_lock:
        write_lock(results, args.lock)
    if args.json:
        print(
            json.dumps(
                [result.__dict__ for result in results],
                indent=2,
            )
        )
    else:
        for result in results:
            print(f"{result.status:>8}  {result.entry_id:<24} {result.detail}")
        present = sum(result.status == "present" for result in results)
        pending = sum(result.status == "pending" for result in results)
        print(f"entries={len(results)} present={present} pending={pending}")
    return 0 if all(result.status in {"present", "pending"} for result in results) else 1


if __name__ == "__main__":
    sys.exit(main())
