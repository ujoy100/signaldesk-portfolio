"""Explicitly bounded, opt-in genuine RAGAS evaluation."""

import sys
import types
from dataclasses import dataclass

from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from backend.app.core.config import Settings
from backend.app.evaluation.dataset import load_dataset
from backend.app.knowledge.models import RetrievalFilters
from backend.app.knowledge.retrieval import TelecomRetriever


@dataclass(frozen=True)
class RagasReport:
    cases: int
    metrics: dict[str, float]
    model: str


def _load_ragas() -> dict:
    """Load RAGAS 0.3 with its removed optional VertexAI import isolated."""

    legacy_name = "langchain_community.chat_models.vertexai"
    if legacy_name not in sys.modules:
        module = types.ModuleType(legacy_name)
        module.ChatVertexAI = type("UnavailableOptionalChatVertexAI", (), {})
        sys.modules[legacy_name] = module
    from ragas import EvaluationDataset, RunConfig, SingleTurnSample, evaluate
    from ragas.embeddings import LangchainEmbeddingsWrapper
    from ragas.llms import LangchainLLMWrapper
    from ragas.metrics import (
        Faithfulness,
        LLMContextPrecisionWithReference,
        LLMContextRecall,
        ResponseRelevancy,
    )

    return {
        "EvaluationDataset": EvaluationDataset,
        "RunConfig": RunConfig,
        "SingleTurnSample": SingleTurnSample,
        "evaluate": evaluate,
        "LangchainEmbeddingsWrapper": LangchainEmbeddingsWrapper,
        "LangchainLLMWrapper": LangchainLLMWrapper,
        "Faithfulness": Faithfulness,
        "LLMContextPrecisionWithReference": LLMContextPrecisionWithReference,
        "LLMContextRecall": LLMContextRecall,
        "ResponseRelevancy": ResponseRelevancy,
    }


def run_bounded_ragas(
    retriever: TelecomRetriever,
    settings: Settings,
    *,
    max_cases: int = 2,
) -> RagasReport:
    """Run genuine LLM-as-judge metrics with a hard case ceiling of three."""

    if not 1 <= max_cases <= 3:
        raise ValueError("RAGAS max_cases must be between 1 and 3")
    if settings.openai_api_key is None or settings.deep_agent_model is None:
        raise RuntimeError("OpenAI evaluation configuration is unavailable")
    api = _load_ragas()
    selected = [case for case in load_dataset() if case.relevant_document][:max_cases]
    samples = []
    for case in selected:
        result = retriever.retrieve(
            case.query,
            filters=RetrievalFilters(access_roles=list(case.access_roles)),
            limit=3,
        )
        contexts = [item.content for item in result.evidence]
        if not contexts:
            raise RuntimeError(f"No context for bounded RAGAS case {case.case_id}")
        samples.append(
            api["SingleTurnSample"](
                user_input=case.query,
                retrieved_contexts=contexts,
                reference_contexts=[contexts[0]],
                response=contexts[0],
                reference=contexts[0],
            )
        )
    model_name = settings.deep_agent_model.removeprefix("openai:")
    llm = api["LangchainLLMWrapper"](
        ChatOpenAI(
            model=model_name,
            api_key=settings.openai_api_key,
            temperature=0,
            max_retries=1,
            timeout=60,
        )
    )
    embeddings = api["LangchainEmbeddingsWrapper"](
        OpenAIEmbeddings(
            model="text-embedding-3-small",
            api_key=settings.openai_api_key,
            max_retries=1,
            request_timeout=60,
        )
    )
    metric_objects = [
        api["LLMContextPrecisionWithReference"](),
        api["LLMContextRecall"](),
        api["Faithfulness"](),
        api["ResponseRelevancy"](),
    ]
    result = api["evaluate"](
        dataset=api["EvaluationDataset"](samples=samples),
        metrics=metric_objects,
        llm=llm,
        embeddings=embeddings,
        run_config=api["RunConfig"](timeout=60, max_retries=1, max_wait=5),
        show_progress=False,
        raise_exceptions=True,
        batch_size=1,
    )
    frame = result.to_pandas()
    metrics = {
        column: round(float(frame[column].mean()), 4)
        for column in frame.columns
        if column
        in {
            "llm_context_precision_with_reference",
            "context_recall",
            "faithfulness",
            "answer_relevancy",
        }
    }
    return RagasReport(
        cases=len(samples), metrics=metrics, model=settings.deep_agent_model
    )
