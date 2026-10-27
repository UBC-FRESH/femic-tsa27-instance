#!/usr/bin/env python3
"""Fetch the TSA 27 TSR corpus into a local, git-ignored directory.

The repository tracks the document metadata in
``metadata/tsr/tsa_documents_with_2022.json`` but not the PDFs. This script reads that
inventory and downloads any missing PDF into ``data/tsr/corpus/tsa/tsa_27/``.

Command-line usage::

    python scripts/fetch_tsr_corpus.py
    python scripts/fetch_tsr_corpus.py --check-only

The download is idempotent: an existing non-empty file is left in place. The script does not
verify a checksum because the public TSR catalogue does not publish one; it records the byte
size from the inventory and reports it.
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.request
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path

ROOT: Path = Path(__file__).resolve().parent.parent
DEFAULT_INVENTORY: Path = ROOT / "metadata" / "tsr" / "tsa_documents_with_2022.json"
DEFAULT_CORPUS: Path = ROOT / "data" / "tsr" / "corpus"
TSA_ID: str = "tsa_27"
USER_AGENT: str = "FEMIC-TSA27-instance/0.1 (+https://github.com/UBC-FRESH/femic-tsa27-instance)"
CHUNK_SIZE: int = 65536


@dataclass(frozen=True)
class Document:
    """One TSR document record from the tracked inventory.

    Attributes
    ----------
    tsa_id : str
        Corpus TSA identifier, for example ``tsa_27``.
    title : str
        Human-readable title.
    relative_path : str
        Source-relative path, for example ``TSR_2010/Data_Package/...pdf``.
    url : str
        Public download URL.
    size_bytes : int or None
        Expected size from the inventory, when known.
    """

    tsa_id: str
    title: str
    relative_path: str
    url: str
    size_bytes: int | None


def load_documents(inventory_path: Path, tsa_id: str = TSA_ID) -> list[Document]:
    """Load the TSA 27 document records from the inventory JSON.

    Parameters
    ----------
    inventory_path : Path
        Path to ``tsa_documents_with_2022.json``.
    tsa_id : str, optional
        TSA identifier to keep. The default is ``tsa_27``.

    Returns
    -------
    list of Document
        The matching document records, in inventory order.

    Raises
    ------
    FileNotFoundError
        When the inventory does not exist.
    ValueError
        When the inventory has no matching documents.
    """
    payload = json.loads(inventory_path.read_text(encoding="utf-8"))
    documents = [
        Document(
            tsa_id=str(item["tsa_id"]),
            title=str(item.get("title") or item.get("file_name") or "untitled"),
            relative_path=str(item["relative_path"]),
            url=str(item["url"]),
            size_bytes=item.get("size_bytes"),
        )
        for item in payload.get("documents", [])
        if str(item.get("tsa_id")) == tsa_id
    ]
    if not documents:
        raise ValueError(f"no documents for {tsa_id} in {inventory_path}")
    return documents


def corpus_path(corpus_root: Path, document: Document) -> Path:
    """Return the local corpus path for one document.

    Parameters
    ----------
    corpus_root : Path
        Root of the local corpus, normally ``data/tsr/corpus``.
    document : Document
        The document record.

    Returns
    -------
    Path
        ``<corpus_root>/tsa/<tsa_id>/<relative_path>``.
    """
    return corpus_root / "tsa" / document.tsa_id / Path(document.relative_path)


def download(url: str, destination: Path) -> int:
    """Download one URL to a destination file.

    Parameters
    ----------
    url : str
        Public URL to fetch.
    destination : Path
        Target file. Parent directories are created.

    Returns
    -------
    int
        Number of bytes written.
    """
    destination.parent.mkdir(parents=True, exist_ok=True)
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    written = 0
    with (
        urllib.request.urlopen(request, timeout=180) as response,
        destination.open("wb") as handle,
    ):
        while chunk := response.read(CHUNK_SIZE):
            handle.write(chunk)
            written += len(chunk)
    return written


def fetch_documents(
    documents: Sequence[Document],
    corpus_root: Path,
    *,
    download_fn: Callable[[str, Path], int] = download,
) -> list[tuple[Document, str]]:
    """Fetch every missing document and report one status per document.

    Parameters
    ----------
    documents : sequence of Document
        Documents to materialize.
    corpus_root : Path
        Root of the local corpus.
    download_fn : callable, optional
        Download function, injected for tests.

    Returns
    -------
    list of tuple of (Document, str)
        One ``(document, status)`` pair per document. Status is ``cached``, ``downloaded``,
        or ``failed``.
    """
    results: list[tuple[Document, str]] = []
    for document in documents:
        destination = corpus_path(corpus_root, document)
        if destination.is_file() and destination.stat().st_size > 0:
            results.append((document, "cached"))
            continue
        try:
            download_fn(document.url, destination)
        except Exception as exc:  # report the URL and the error to the caller
            results.append((document, f"failed: {exc}"))
        else:
            results.append((document, "downloaded"))
    return results


def main(argv: Sequence[str] | None = None) -> int:
    """Run the corpus fetch from the command line.

    Parameters
    ----------
    argv : sequence of str or None, optional
        Command-line arguments. ``None`` uses ``sys.argv``.

    Returns
    -------
    int
        ``0`` when every document is cached or downloaded, ``1`` otherwise.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inventory", type=Path, default=DEFAULT_INVENTORY)
    parser.add_argument("--corpus-root", type=Path, default=DEFAULT_CORPUS)
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Report missing documents without downloading them.",
    )
    args = parser.parse_args(argv)
    documents = load_documents(args.inventory)
    if args.check_only:
        missing = [d for d in documents if not corpus_path(args.corpus_root, d).is_file()]
        print(f"documents={len(documents)} missing={len(missing)}")
        return 0 if not missing else 1
    results = fetch_documents(documents, args.corpus_root)
    counts: dict[str, int] = {}
    for _, status in results:
        counts[status] = counts.get(status, 0) + 1
    for document, status in results:
        print(f"{status:>12}  {document.relative_path}")
    print(f"documents={len(results)} statuses={counts}")
    return 0 if all(not status.startswith("failed") for _, status in results) else 1


if __name__ == "__main__":
    sys.exit(main())
