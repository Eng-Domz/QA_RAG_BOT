from pathlib import Path

from document_loader import DocumentProcessor


def test_nested_duplicate_filenames_get_distinct_stable_ids(tmp_path: Path):
    first = tmp_path / "course-a" / "lecture.txt"
    second = tmp_path / "course-b" / "lecture.txt"
    first.parent.mkdir()
    second.parent.mkdir()
    first.write_text("alpha " * 40, encoding="utf-8")
    second.write_text("beta " * 40, encoding="utf-8")

    processor = DocumentProcessor(chunk_size=80, chunk_overlap=10)
    chunks = processor.process(str(tmp_path))

    source_paths = {chunk.metadata["source_path"] for chunk in chunks}
    chunk_ids = [chunk.metadata["chunk_id"] for chunk in chunks]
    assert source_paths == {"course-a/lecture.txt", "course-b/lecture.txt"}
    assert len(chunk_ids) == len(set(chunk_ids))

    repeated = processor.process(str(tmp_path))
    assert [chunk.metadata["chunk_id"] for chunk in chunks] == [
        chunk.metadata["chunk_id"] for chunk in repeated
    ]


def test_content_change_changes_source_hash_and_chunk_id(tmp_path: Path):
    source = tmp_path / "lecture.txt"
    source.write_text("first version", encoding="utf-8")
    processor = DocumentProcessor(chunk_size=100, chunk_overlap=10)
    original = processor.process(str(tmp_path))[0]

    source.write_text("second version", encoding="utf-8")
    changed = processor.process(str(tmp_path))[0]

    assert original.metadata["source_hash"] != changed.metadata["source_hash"]
    assert original.metadata["chunk_id"] != changed.metadata["chunk_id"]


def test_file_hashing_does_not_use_read_bytes(tmp_path: Path, monkeypatch):
    source = tmp_path / "large-lecture.txt"
    source.write_text("streamed content " * 1000, encoding="utf-8")

    def reject_read_bytes(_path):
        raise AssertionError("read_bytes would load the entire file into memory")

    monkeypatch.setattr(Path, "read_bytes", reject_read_bytes)
    chunks = DocumentProcessor(chunk_size=500, chunk_overlap=50).process(str(tmp_path))

    assert chunks
    assert all(chunk.metadata["source_hash"] for chunk in chunks)
