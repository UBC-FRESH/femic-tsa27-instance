"""Tests for the public-data manifest verifier."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

import verify_public_data
from verify_public_data import Result


def write_manifest(path: Path, entries: list[dict[str, object]]) -> None:
    """Write a minimal manifest for the tests.

    Parameters
    ----------
    path : Path
        Destination path.
    entries : list of dict
        Manifest entries.
    """
    path.write_text(yaml.safe_dump({"entries": entries}), encoding="utf-8")


def test_load_manifest_rejects_missing_entries(tmp_path: Path) -> None:
    """A manifest without an entries list is rejected."""
    path = tmp_path / "manifest.yaml"
    path.write_text("schema_version: 1\n", encoding="utf-8")
    with pytest.raises(ValueError, match="entries"):
        verify_public_data.load_manifest(path)


def test_load_manifest_returns_entries(tmp_path: Path) -> None:
    """A valid manifest loads its entries."""
    path = tmp_path / "manifest.yaml"
    write_manifest(path, [{"id": "a", "status": "to_fetch"}])
    assert verify_public_data.load_manifest(path)["entries"][0]["id"] == "a"


def test_resolve_path_prefers_mirror(tmp_path: Path) -> None:
    """An existing mirror path wins over the instance-local path."""
    mirror = tmp_path / "mirror"
    (mirror / "bc" / "vri").mkdir(parents=True)
    target = mirror / "bc" / "vri" / "vri.gdb"
    target.write_text("x", encoding="utf-8")
    entry = {"mirror_path": "bc/vri/vri.gdb", "local_path": "data/bc/vri/vri.gdb"}
    resolved = verify_public_data.resolve_path(entry, tmp_path, mirror)
    assert resolved == target


def test_resolve_path_falls_back_to_local(tmp_path: Path) -> None:
    """Without a mirror hit, the local path is returned."""
    entry = {"mirror_path": "bc/vri/vri.gdb", "local_path": "data/bc/vri/vri.gdb"}
    resolved = verify_public_data.resolve_path(entry, tmp_path, tmp_path / "missing")
    assert resolved == tmp_path / "data" / "bc" / "vri" / "vri.gdb"


def test_resolve_path_returns_none_without_paths(tmp_path: Path) -> None:
    """An entry with no path resolves to None."""
    assert verify_public_data.resolve_path({"id": "x"}, tmp_path, None) is None


def test_digest_path_file(tmp_path: Path) -> None:
    """A file digest is the SHA-256 of its bytes."""
    path = tmp_path / "file.bin"
    path.write_bytes(b"abc")
    digest, size, count = verify_public_data.digest_path(path)
    assert size == 3
    assert count == 1
    assert digest == "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"


def test_digest_path_directory(tmp_path: Path) -> None:
    """A directory digest covers the sorted relative paths and sizes."""
    root = tmp_path / "gdb"
    root.mkdir()
    (root / "a").write_bytes(b"1")
    (root / "b").write_bytes(b"22")
    digest, size, count = verify_public_data.digest_path(root)
    assert size == 3
    assert count == 2
    assert len(digest) == 64


def test_digest_path_missing(tmp_path: Path) -> None:
    """A missing path raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        verify_public_data.digest_path(tmp_path / "missing")


def test_count_corpus_documents(tmp_path: Path) -> None:
    """The corpus count includes nested PDFs and ignores other files."""
    (tmp_path / "a").mkdir()
    (tmp_path / "a" / "one.pdf").write_bytes(b"x")
    (tmp_path / "two.pdf").write_bytes(b"x")
    (tmp_path / "two.txt").write_bytes(b"x")
    assert verify_public_data.count_corpus_documents(tmp_path) == 2
    assert verify_public_data.count_corpus_documents(tmp_path / "missing") == 0


def test_display_path_labels(tmp_path: Path) -> None:
    """Mirror and local paths get portable labels."""
    mirror = tmp_path / "mirror"
    mirror.mkdir()
    mirror_file = mirror / "bc" / "vri.gdb"
    mirror_file.parent.mkdir()
    mirror_file.write_text("x", encoding="utf-8")
    local_file = tmp_path / "data" / "file.bin"
    local_file.parent.mkdir()
    local_file.write_text("x", encoding="utf-8")
    assert verify_public_data.display_path(mirror_file, tmp_path, mirror) == "mirror:bc/vri.gdb"
    assert verify_public_data.display_path(local_file, tmp_path, mirror) == "local:data/file.bin"


def test_display_path_falls_back_to_name(tmp_path: Path) -> None:
    """A path outside both roots is reported by name."""
    outside = tmp_path / "outside.bin"
    outside.write_text("x", encoding="utf-8")
    assert verify_public_data.display_path(outside, tmp_path / "root", None) == "outside.bin"


def test_verify_entry_available_file(tmp_path: Path) -> None:
    """An available file is present with a digest."""
    path = tmp_path / "data" / "file.bin"
    path.parent.mkdir()
    path.write_bytes(b"abc")
    entry = {"id": "file", "status": "available", "local_path": "data/file.bin"}
    result = verify_public_data.verify_entry(entry, tmp_path, None)
    assert result.status == "present"
    assert result.file_count == 1
    assert len(result.digest) == 64


def test_verify_entry_to_fetch() -> None:
    """A to_fetch entry is pending, not a failure."""
    result = verify_public_data.verify_entry({"id": "bec", "status": "to_fetch"}, Path("."), None)
    assert result.status == "pending"


def test_verify_entry_missing(tmp_path: Path) -> None:
    """A missing path is reported as missing."""
    entry = {"id": "file", "status": "available", "local_path": "data/missing.bin"}
    result = verify_public_data.verify_entry(entry, tmp_path, None)
    assert result.status == "missing"


def test_verify_entry_no_path() -> None:
    """An available entry without a path is missing."""
    result = verify_public_data.verify_entry({"id": "x", "status": "available"}, Path("."), None)
    assert result.status == "missing"


def test_verify_entry_corpus_present(tmp_path: Path) -> None:
    """A corpus with the expected count is present."""
    corpus = tmp_path / "corpus"
    corpus.mkdir()
    (corpus / "one.pdf").write_bytes(b"x")
    entry = {
        "id": "tsr",
        "status": "available",
        "local_path": "corpus",
        "check": "tsr_corpus",
        "expected_count": 1,
    }
    result = verify_public_data.verify_entry(entry, tmp_path, None)
    assert result.status == "present"
    assert result.file_count == 1


def test_verify_entry_corpus_mismatch(tmp_path: Path) -> None:
    """A corpus with the wrong count is a mismatch."""
    corpus = tmp_path / "corpus"
    corpus.mkdir()
    (corpus / "one.pdf").write_bytes(b"x")
    entry = {
        "id": "tsr",
        "status": "available",
        "local_path": "corpus",
        "check": "tsr_corpus",
        "expected_count": 2,
    }
    result = verify_public_data.verify_entry(entry, tmp_path, None)
    assert result.status == "mismatch"


def test_write_lock(tmp_path: Path) -> None:
    """The lock records every result, including pending entries."""
    lock = tmp_path / "lock.yaml"
    verify_public_data.write_lock(
        [Result("a", "present", "path", "abc", 1, 1), Result("b", "pending", "to_fetch")],
        lock,
    )
    payload = yaml.safe_load(lock.read_text(encoding="utf-8"))
    assert payload["entries"]["a"]["sha256"] == "abc"
    assert payload["entries"]["b"]["status"] == "pending"


def test_main_json_and_lock(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """The CLI writes the lock and emits JSON."""
    monkeypatch.setattr(verify_public_data, "ROOT", tmp_path)
    path = tmp_path / "data" / "file.bin"
    path.parent.mkdir()
    path.write_bytes(b"abc")
    manifest = tmp_path / "manifest.yaml"
    write_manifest(
        manifest,
        [{"id": "file", "status": "available", "local_path": "data/file.bin"}],
    )
    lock = tmp_path / "lock.yaml"
    code = verify_public_data.main(
        ["--manifest", str(manifest), "--lock", str(lock), "--write-lock", "--json"]
    )
    assert code == 0
    assert lock.is_file()
    assert '"status": "present"' in capsys.readouterr().out


def test_main_reports_missing(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """The CLI returns non-zero when an available entry is missing."""
    manifest = tmp_path / "manifest.yaml"
    write_manifest(
        manifest, [{"id": "file", "status": "available", "local_path": "data/missing.bin"}]
    )
    code = verify_public_data.main(["--manifest", str(manifest)])
    assert code == 1
    assert "missing" in capsys.readouterr().out
