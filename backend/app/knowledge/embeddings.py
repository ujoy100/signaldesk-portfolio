"""Deterministic, credential-free LangChain embeddings for local development."""

import hashlib
import math
import re
from itertools import pairwise

from langchain_core.embeddings import Embeddings

TOKEN_PATTERN = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
SEMANTIC_ALIASES = {
    "abroad": "roaming",
    "activate": "activation",
    "activated": "activation",
    "activation": "activation",
    "bill": "billing",
    "card": "sim",
    "charged": "billing",
    "charges": "billing",
    "connectivity": "network",
    "internet": "data",
    "invoice": "billing",
    "overseas": "roaming",
    "pin": "puk",
    "signal": "network",
    "start": "activation",
    "travelling": "roaming",
    "traveling": "roaming",
}


def tokenize(text: str) -> list[str]:
    """Normalize telecom text into stable lexical features."""

    tokens = TOKEN_PATTERN.findall(text.lower())
    return [SEMANTIC_ALIASES.get(token, token) for token in tokens]


class DeterministicTelecomEmbeddings(Embeddings):
    """Feature-hashing embeddings implementing LangChain's embedding contract.

    This is an offline development baseline, not a claim of model-grade semantic
    quality. It keeps ingestion deterministic and requires no external API key.
    """

    def __init__(self, dimensions: int = 384) -> None:
        self.dimensions = dimensions

    def _embed(self, text: str) -> list[float]:
        vector = [0.0] * self.dimensions
        tokens = tokenize(text)
        features = tokens + [f"{left}_{right}" for left, right in pairwise(tokens)]
        for feature in features:
            digest = hashlib.sha256(feature.encode("utf-8")).digest()
            index = int.from_bytes(digest[:4], "big") % self.dimensions
            vector[index] += 1.0
        norm = math.sqrt(sum(value * value for value in vector))
        return [value / norm for value in vector] if norm else vector

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._embed(text) for text in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._embed(text)
