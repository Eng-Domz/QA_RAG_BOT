import pytest
from langchain_core.documents import Document

from vectorstore import VectorStoreManager


def make_document(source: str, source_hash: str, chunk_id: str) -> Document:
    return Document(
        page_content=f"content-{chunk_id}",
        metadata={
            "source_file": source.rsplit("/", 1)[-1],
            "source_path": source,
            "source_hash": source_hash,
            "chunk_id": chunk_id,
        },
    )


class FakeCollection:
    def __init__(self, store):
        self.store = store

    def get(self, include):
        return {
            "ids": list(self.store.items),
            "metadatas": [item.metadata for item in self.store.items.values()],
        }


class FakeStore:
    def __init__(self):
        self.items = {}
        self._collection = FakeCollection(self)
        self.fail_after_add = False

    def add_documents(self, documents, ids):
        self.items.update(dict(zip(ids, documents)))
        if self.fail_after_add:
            self.fail_after_add = False
            raise RuntimeError("simulated embedding failure after partial add")

    def delete(self, ids):
        for item_id in ids:
            self.items.pop(item_id, None)


def manager_with_fake_store():
    manager = object.__new__(VectorStoreManager)
    manager.vectorstore = FakeStore()
    return manager


def test_repeated_sync_is_idempotent():
    manager = manager_with_fake_store()
    documents = [make_document("a/lecture.txt", "hash-a", "chunk-a")]

    assert manager._synchronize_documents(documents) == {
        "added": 1,
        "removed": 0,
        "unchanged": 0,
    }
    assert manager._synchronize_documents(documents) == {
        "added": 0,
        "removed": 0,
        "unchanged": 1,
    }
    assert list(manager.vectorstore.items) == ["chunk-a"]


def test_changed_and_deleted_sources_are_synchronized():
    manager = manager_with_fake_store()
    manager._synchronize_documents(
        [
            make_document("a/lecture.txt", "old", "old-a"),
            make_document("b/lecture.txt", "hash-b", "chunk-b"),
        ]
    )

    stats = manager._synchronize_documents(
        [make_document("a/lecture.txt", "new", "new-a")]
    )

    assert stats == {"added": 1, "removed": 2, "unchanged": 0}
    assert list(manager.vectorstore.items) == ["new-a"]


def test_failed_replacement_preserves_old_indexed_source():
    manager = manager_with_fake_store()
    old = make_document("a/lecture.txt", "old", "old-a")
    manager._synchronize_documents([old])
    manager.vectorstore.fail_after_add = True

    with pytest.raises(RuntimeError, match="old chunks remain indexed"):
        manager._synchronize_documents(
            [make_document("a/lecture.txt", "new", "new-a")]
        )

    assert list(manager.vectorstore.items) == ["old-a"]
    assert manager.vectorstore.items["old-a"].metadata["source_hash"] == "old"


def test_empty_corpus_intentionally_clears_stale_index():
    manager = manager_with_fake_store()
    manager._synchronize_documents(
        [make_document("a/lecture.txt", "hash-a", "chunk-a")]
    )

    assert manager._synchronize_documents([]) == {
        "added": 0,
        "removed": 1,
        "unchanged": 0,
    }
    assert manager.vectorstore.items == {}
