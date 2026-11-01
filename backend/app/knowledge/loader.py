"""LangChain loader and deterministic splitter for fictional knowledge."""

import json
from collections.abc import Iterator
from pathlib import Path

from langchain_core.document_loaders import BaseLoader
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from backend.app.knowledge.models import KnowledgeRecord

DEFAULT_KNOWLEDGE_PATH = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "knowledge"
    / "fictional_telecom.json"
)


class TelecomKnowledgeLoader(BaseLoader):
    """Load and validate the repository's fictional telecom JSON corpus."""

    def __init__(self, path: Path = DEFAULT_KNOWLEDGE_PATH) -> None:
        self.path = path

    def lazy_load(self) -> Iterator[Document]:
        records = json.loads(self.path.read_text(encoding="utf-8"))
        for raw_record in records:
            record = KnowledgeRecord.model_validate(raw_record)
            yield Document(
                page_content=record.content,
                metadata=record.metadata.model_dump(),
            )


def load_knowledge_chunks(
    path: Path = DEFAULT_KNOWLEDGE_PATH,
    *,
    chunk_size: int = 600,
    chunk_overlap: int = 80,
) -> list[Document]:
    """Load source records and split them with stable chunk indexes."""

    documents = TelecomKnowledgeLoader(path).load()
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    chunks: list[Document] = []
    for document in documents:
        for chunk_index, chunk in enumerate(splitter.split_documents([document])):
            chunk.metadata["chunk_index"] = chunk_index
            chunks.append(chunk)
    return chunks
