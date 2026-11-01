"""Dense, keyword, hybrid, and reranked telecom knowledge retrieval."""

from collections import defaultdict
from dataclasses import dataclass
from time import perf_counter

from qdrant_client import QdrantClient, models
from rank_bm25 import BM25Okapi

from backend.app.knowledge.embeddings import DeterministicTelecomEmbeddings, tokenize
from backend.app.knowledge.models import (
    Evidence,
    RetrievalFilters,
    RetrievalResponse,
)
from backend.app.observability import TelemetryRecorder

STOPWORDS = {
    "a",
    "an",
    "and",
    "can",
    "do",
    "does",
    "explain",
    "for",
    "got",
    "how",
    "i",
    "is",
    "it",
    "my",
    "new",
    "of",
    "on",
    "the",
    "to",
    "using",
    "what",
}


def _meaningful_tokens(text: str) -> list[str]:
    return [token for token in tokenize(text) if token not in STOPWORDS]


@dataclass(frozen=True)
class RankedChunk:
    chunk_id: str
    payload: dict
    score: float
    signals: tuple[str, ...]


def _qdrant_filter(filters: RetrievalFilters) -> models.Filter:
    conditions: list[models.Condition] = []
    if filters.active_only:
        conditions.append(
            models.FieldCondition(key="active", match=models.MatchValue(value=True))
        )
    if filters.service:
        conditions.append(
            models.FieldCondition(
                key="service", match=models.MatchValue(value=filters.service)
            )
        )
    if filters.category:
        conditions.append(
            models.FieldCondition(
                key="category", match=models.MatchValue(value=filters.category)
            )
        )
    if filters.version:
        conditions.append(
            models.FieldCondition(
                key="version", match=models.MatchValue(value=filters.version)
            )
        )
    conditions.append(
        models.FieldCondition(
            key="access_roles",
            match=models.MatchAny(any=filters.access_roles),
        )
    )
    return models.Filter(must=conditions)


class TelecomRetriever:
    """Retrieve evidence using measurable vector and lexical signals."""

    def __init__(
        self,
        client: QdrantClient,
        collection_name: str,
        embeddings: DeterministicTelecomEmbeddings,
        *,
        minimum_score: float = 0.18,
        telemetry_recorder: TelemetryRecorder | None = None,
    ) -> None:
        self.client = client
        self.collection_name = collection_name
        self.embeddings = embeddings
        self.minimum_score = minimum_score
        self.telemetry = telemetry_recorder

    def _dense(
        self, query: str, filters: RetrievalFilters, limit: int
    ) -> list[RankedChunk]:
        response = self.client.query_points(
            collection_name=self.collection_name,
            query=self.embeddings.embed_query(query),
            query_filter=_qdrant_filter(filters),
            with_payload=True,
            limit=limit,
        )
        return [
            RankedChunk(str(point.id), point.payload or {}, point.score, ("vector",))
            for point in response.points
        ]

    def _eligible_chunks(self, filters: RetrievalFilters) -> list[RankedChunk]:
        records, offset = self.client.scroll(
            collection_name=self.collection_name,
            scroll_filter=_qdrant_filter(filters),
            limit=256,
            with_payload=True,
        )
        while offset is not None:
            page, offset = self.client.scroll(
                collection_name=self.collection_name,
                scroll_filter=_qdrant_filter(filters),
                limit=256,
                offset=offset,
                with_payload=True,
            )
            records.extend(page)
        return [
            RankedChunk(str(record.id), record.payload or {}, 0.0, ("keyword",))
            for record in records
        ]

    def _keyword(
        self, query: str, filters: RetrievalFilters, limit: int
    ) -> list[RankedChunk]:
        candidates = self._eligible_chunks(filters)
        query_tokens = _meaningful_tokens(query)
        if not candidates or not query_tokens:
            return []
        corpus = [tokenize(chunk.payload["content"]) for chunk in candidates]
        scores = BM25Okapi(corpus).get_scores(query_tokens)
        query_token_set = set(query_tokens)
        adjusted_scores = [
            float(score)
            + 10.0
            * len(
                {
                    token
                    for token in query_token_set & set(document_tokens)
                    if "-" in token or any(character.isdigit() for character in token)
                }
            )
            for score, document_tokens in zip(scores, corpus, strict=True)
        ]
        ranked = sorted(
            (
                RankedChunk(chunk.chunk_id, chunk.payload, float(score), ("keyword",))
                for chunk, score in zip(candidates, adjusted_scores, strict=True)
                if score > 0
            ),
            key=lambda chunk: (-chunk.score, chunk.chunk_id),
        )
        if not ranked:
            return []
        maximum = ranked[0].score
        return [
            RankedChunk(
                chunk.chunk_id, chunk.payload, chunk.score / maximum, chunk.signals
            )
            for chunk in ranked[:limit]
        ]

    @staticmethod
    def _hybrid(
        dense: list[RankedChunk], keyword: list[RankedChunk], limit: int
    ) -> list[RankedChunk]:
        scores: defaultdict[str, float] = defaultdict(float)
        chunks: dict[str, RankedChunk] = {}
        signals: defaultdict[str, set[str]] = defaultdict(set)
        for result_set in (dense, keyword):
            for rank, chunk in enumerate(result_set, start=1):
                scores[chunk.chunk_id] += 1.0 / (60 + rank)
                chunks[chunk.chunk_id] = chunk
                signals[chunk.chunk_id].update(chunk.signals)
        ranked_ids = sorted(scores, key=lambda item: (-scores[item], item))[:limit]
        max_score = scores[ranked_ids[0]] if ranked_ids else 1.0
        return [
            RankedChunk(
                chunk_id,
                chunks[chunk_id].payload,
                scores[chunk_id] / max_score,
                tuple(sorted(signals[chunk_id])),
            )
            for chunk_id in ranked_ids
        ]

    @staticmethod
    def _rerank(query: str, chunks: list[RankedChunk]) -> list[RankedChunk]:
        query_terms = set(_meaningful_tokens(query))
        reranked = []
        for chunk in chunks:
            content_terms = set(_meaningful_tokens(chunk.payload["content"]))
            coverage = len(query_terms & content_terms) / max(len(query_terms), 1)
            phrase_bonus = (
                0.15 if query.lower() in chunk.payload["content"].lower() else 0.0
            )
            score = 0.65 * chunk.score + 0.35 * coverage + phrase_bonus
            reranked.append(
                RankedChunk(
                    chunk.chunk_id,
                    chunk.payload,
                    min(score, 1.0),
                    (*chunk.signals, "deterministic_cross_signal_reranker"),
                )
            )
        return sorted(reranked, key=lambda chunk: (-chunk.score, chunk.chunk_id))

    @staticmethod
    def _evidence(chunk: RankedChunk) -> Evidence:
        payload = chunk.payload
        return Evidence(
            chunk_id=chunk.chunk_id,
            document_id=payload["document_id"],
            source=payload["source"],
            title=payload["title"],
            section=payload["section"],
            page=payload.get("page"),
            version=payload["version"],
            service=payload["service"],
            category=payload["category"],
            content=payload["content"],
            score=round(chunk.score, 6),
            retrieval_signals=list(chunk.signals),
        )

    def retrieve(
        self,
        query: str,
        *,
        strategy: str = "hybrid_reranked",
        filters: RetrievalFilters | None = None,
        limit: int = 4,
    ) -> RetrievalResponse:
        """Return filtered evidence or an explicit insufficient-evidence result."""

        started = perf_counter()
        selected_filters = filters or RetrievalFilters()
        candidate_limit = max(limit * 3, 10)
        dense = self._dense(query, selected_filters, candidate_limit)
        keyword = self._keyword(query, selected_filters, candidate_limit)
        if (
            strategy.startswith("hybrid")
            and not keyword
            and (not dense or dense[0].score < self.minimum_score)
        ):
            response = RetrievalResponse(
                answered=False,
                strategy=strategy,
                evidence=[],
                reason="Insufficient indexed evidence for this question and access scope.",
            )
            if self.telemetry:
                self.telemetry.record(
                    "retrieval.query", started=started, answered=False, evidence_count=0
                )
            return response
        if strategy == "vector":
            ranked = dense
        elif strategy == "keyword":
            ranked = keyword
        elif strategy == "hybrid":
            ranked = self._hybrid(dense, keyword, candidate_limit)
        elif strategy == "hybrid_reranked":
            ranked = self._rerank(query, self._hybrid(dense, keyword, candidate_limit))
        else:
            raise ValueError(f"Unknown retrieval strategy: {strategy}")

        query_terms = set(_meaningful_tokens(query))
        required_identifiers = {
            token
            for token in query_terms
            if "-" in token or any(character.isdigit() for character in token)
        }
        minimum_query_coverage = 0.4
        qualified = [
            chunk
            for chunk in ranked
            if chunk.score >= self.minimum_score
            and len(
                query_terms.intersection(_meaningful_tokens(chunk.payload["content"]))
            )
            / max(len(query_terms), 1)
            >= minimum_query_coverage
            and required_identifiers.issubset(
                set(_meaningful_tokens(chunk.payload["content"]))
            )
        ][:limit]
        if not qualified:
            response = RetrievalResponse(
                answered=False,
                strategy=strategy,
                evidence=[],
                reason="Insufficient indexed evidence for this question and access scope.",
            )
            if self.telemetry:
                self.telemetry.record(
                    "retrieval.query", started=started, answered=False, evidence_count=0
                )
            return response
        response = RetrievalResponse(
            answered=True,
            strategy=strategy,
            evidence=[self._evidence(chunk) for chunk in qualified],
        )
        if self.telemetry:
            self.telemetry.record(
                "retrieval.query",
                started=started,
                answered=True,
                evidence_count=len(response.evidence),
                strategy=strategy,
            )
        return response
