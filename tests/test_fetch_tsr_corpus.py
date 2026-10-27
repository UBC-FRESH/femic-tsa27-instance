"""Tests for the TSR corpus fetch helper."""

from __future__ import annotations

import json
import urllib.request
from pathlib import Path

import pytest

import fetch_tsr_corpus
from fetch_tsr_corpus import Document


class FakeResponse:
    """Minimal context-managed HTTP response for download tests."""

    def __init__(self, data: bytes) -> None:
        """Store the bytes that ``read`` should return.

        Parameters
        ----------
        data : bytes
            Response body.
        """
        self._data = data
        self._offset = 0

    def read(self, size: int = -1) -> bytes:
        """Return the next chunk of the response body.

        Parameters
        ----------
        size : int, optional
            Maximum bytes to return. ``-1`` returns the remainder.

        Returns
        -------
        bytes
            The next chunk.
        """
        if size < 0:
            chunk = self._data[self._offset :]
            self._offset = len(self._data)
            return chunk
        chunk = self._data[self._offset : self._offset + size]
        self._offset += len(chunk)
        return chunk

    def __enter__(self) -> FakeResponse:
        """Return the response for a ``with`` block."""
        return self

    def __exit__(self, *args: object) -> None:
        """Leave the ``with`` block without suppressing exceptions."""
        return None


def write_inventory(path: Path) -> None:
    """Write a small two-TSA inventory for the tests.

    Parameters
    ----------
    path : Path
        Destination JSON path.
    """
    path.write_text(
        json.dumps(
            {
                "document_count": 2,
                "documents": [
                    {
                        "tsa_id": "tsa_27",
                        "title": "TSR4 data package",
                        "relative_path": "TSR_2010/Data_Package/example.pdf",
                        "url": "https://example.invalid/27.pdf",
                        "size_bytes": 123,
                    },
                    {
                        "tsa_id": "tsa_08",
                        "title": "Other TSA",
                        "relative_path": "TSR_2010/Other.pdf",
                        "url": "https://example.invalid/08.pdf",
                        "size_bytes": 456,
                    },
                ],
            }
        ),
        encoding="utf-8",
    )


def test_load_documents_filters_by_tsa(tmp_path: Path) -> None:
    """Only the requested TSA's documents are returned."""
    inventory = tmp_path / "docs.json"
    write_inventory(inventory)
    documents = fetch_tsr_corpus.load_documents(inventory)
    assert len(documents) == 1
    assert documents[0].tsa_id == "tsa_27"
    assert documents[0].title == "TSR4 data package"


def test_load_documents_rejects_empty_tsa(tmp_path: Path) -> None:
    """An inventory without the requested TSA is an error, not an empty list."""
    inventory = tmp_path / "docs.json"
    write_inventory(inventory)
    with pytest.raises(ValueError, match="tsa_99"):
        fetch_tsr_corpus.load_documents(inventory, tsa_id="tsa_99")


def test_corpus_path_is_repo_relative(tmp_path: Path) -> None:
    """The corpus path nests the TSA id and the source-relative path."""
    document = Document(
        tsa_id="tsa_27",
        title="t",
        relative_path="TSR_2022/Data_Package/27.pdf",
        url="https://example.invalid/27.pdf",
        size_bytes=None,
    )
    path = fetch_tsr_corpus.corpus_path(tmp_path, document)
    assert path == tmp_path / "tsa" / "tsa_27" / "TSR_2022" / "Data_Package" / "27.pdf"


def test_download_writes_bytes(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """The download helper writes the response body and returns its size."""
    monkeypatch.setattr(
        urllib.request,
        "urlopen",
        lambda request, timeout: FakeResponse(b"abc123"),
    )
    destination = tmp_path / "nested" / "file.pdf"
    written = fetch_tsr_corpus.download("https://example.invalid/file.pdf", destination)
    assert written == 6
    assert destination.read_bytes() == b"abc123"


def test_fetch_documents_skips_cached(tmp_path: Path) -> None:
    """An existing non-empty file is reported as cached and not downloaded."""
    document = Document("tsa_27", "t", "a.pdf", "https://example.invalid/a.pdf", 1)
    cached = fetch_tsr_corpus.corpus_path(tmp_path, document)
    cached.parent.mkdir(parents=True)
    cached.write_bytes(b"x")
    results = fetch_tsr_corpus.fetch_documents(
        [document],
        tmp_path,
        download_fn=lambda url, path: pytest.fail("download should not be called"),
    )
    assert results == [(document, "cached")]


def test_fetch_documents_downloads_missing(tmp_path: Path) -> None:
    """A missing file is downloaded and reported as downloaded."""
    document = Document("tsa_27", "t", "a.pdf", "https://example.invalid/a.pdf", 1)

    def fake_download(url: str, destination: Path) -> int:
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(b"x")
        return 1

    results = fetch_tsr_corpus.fetch_documents([document], tmp_path, download_fn=fake_download)
    assert results == [(document, "downloaded")]


def test_fetch_documents_reports_failure(tmp_path: Path) -> None:
    """A download error is reported with the document and the error."""
    document = Document("tsa_27", "t", "a.pdf", "https://example.invalid/a.pdf", 1)

    def broken_download(url: str, destination: Path) -> int:
        raise OSError("network down")

    results = fetch_tsr_corpus.fetch_documents([document], tmp_path, download_fn=broken_download)
    assert results[0][0] == document
    assert results[0][1].startswith("failed: network down")


def test_main_check_only_reports_missing(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """``--check-only`` returns non-zero when a document is missing."""
    inventory = tmp_path / "docs.json"
    write_inventory(inventory)
    code = fetch_tsr_corpus.main(
        ["--inventory", str(inventory), "--corpus-root", str(tmp_path / "corpus"), "--check-only"]
    )
    assert code == 1
    assert "missing=1" in capsys.readouterr().out


def test_main_check_only_succeeds_when_complete(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """``--check-only`` returns zero when every document is present."""
    inventory = tmp_path / "docs.json"
    write_inventory(inventory)
    corpus = tmp_path / "corpus"
    document = fetch_tsr_corpus.load_documents(inventory)[0]
    target = fetch_tsr_corpus.corpus_path(corpus, document)
    target.parent.mkdir(parents=True)
    target.write_bytes(b"x")
    code = fetch_tsr_corpus.main(
        ["--inventory", str(inventory), "--corpus-root", str(corpus), "--check-only"]
    )
    assert code == 0
    assert "missing=0" in capsys.readouterr().out


def test_main_fetch_reports_status(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The fetch path prints one status per document and returns zero on success."""
    inventory = tmp_path / "docs.json"
    write_inventory(inventory)
    document = fetch_tsr_corpus.load_documents(inventory)[0]
    monkeypatch.setattr(
        fetch_tsr_corpus,
        "fetch_documents",
        lambda documents, corpus_root: [(documents[0], "downloaded")],
    )
    code = fetch_tsr_corpus.main(
        ["--inventory", str(inventory), "--corpus-root", str(tmp_path / "corpus")]
    )
    output = capsys.readouterr().out
    assert code == 0
    assert "downloaded" in output
    assert document.relative_path in output


def test_main_fetch_returns_one_on_failure(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """The fetch path returns non-zero when any document fails."""
    inventory = tmp_path / "docs.json"
    write_inventory(inventory)
    monkeypatch.setattr(
        fetch_tsr_corpus,
        "fetch_documents",
        lambda documents, corpus_root: [(documents[0], "failed: boom")],
    )
    code = fetch_tsr_corpus.main(
        ["--inventory", str(inventory), "--corpus-root", str(tmp_path / "corpus")]
    )
    assert code == 1
