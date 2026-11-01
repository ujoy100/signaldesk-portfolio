"""Phase 10 bounded Deep Agents routing and safe-failure tests."""

import asyncio

import pytest
from langgraph.checkpoint.memory import InMemorySaver
from pydantic import SecretStr

from backend.app.knowledge.models import Evidence, RetrievalResponse
from backend.app.mcp.contracts import GatewayPrincipal, GatewayResponse
from backend.app.schemas.support import (
    InvestigationFinding,
    InvestigationResult,
    InvestigationToolCall,
    ResolutionEvidence,
)
from backend.app.workflow.graph import SupportWorkflow
from backend.app.workflow.investigation import (
    READ_ONLY_TOOLS,
    DeepAgentInvestigator,
    InvestigationUnavailable,
)


class RecordingRetriever:
    def __init__(self) -> None:
        self.filters = None

    def retrieve(self, query: str, **kwargs: object) -> RetrievalResponse:
        self.filters = kwargs.get("filters")
        return RetrievalResponse(
            answered=True,
            strategy="hybrid_reranked",
            evidence=[
                Evidence(
                    chunk_id="sim-evidence",
                    document_id="sim-guide",
                    source="fictional",
                    title="SIM activation",
                    section="activation",
                    page=1,
                    version="1.0",
                    service="mobile",
                    category="activation",
                    content="Restart after activation.",
                    score=0.9,
                    retrieval_signals=["vector"],
                )
            ],
        )


class ForbiddenGateway:
    async def invoke(self, *args: object, **kwargs: object) -> GatewayResponse:
        raise AssertionError("simple flow must not invoke an investigation tool")


class RecordingInvestigator:
    def __init__(self, *, fail: bool = False) -> None:
        self.calls = 0
        self.fail = fail

    async def investigate(self, **kwargs: object) -> InvestigationResult:
        self.calls += 1
        if self.fail:
            raise InvestigationUnavailable("offline")
        evidence = ResolutionEvidence(
            source_type="ticket",
            source_id="gateway-ticket-1",
            title="Historical roaming failures",
            content="Validated read-only ticket history.",
            signals=["mcp_gateway", "deep_agent"],
        )
        return InvestigationResult(
            issue_classification="roaming",
            investigation_summary="Repeated failures need an eligibility review.",
            supporting_evidence=[evidence],
            citations=[evidence.source_id],
            tool_calls_performed=[
                InvestigationToolCall(
                    tool="ticket.get_ticket_history",
                    request_id=evidence.source_id,
                    purpose="Compare historical failures",
                )
            ],
            findings=[
                InvestigationFinding(
                    finding="Failures recur", evidence_ids=[evidence.source_id]
                )
            ],
            uncertainties=["Current visited network status is unknown."],
            recommended_next_steps=["Escalate to roaming operations."],
            status="completed",
        )


def _state(issue: str, thread_id: str) -> dict:
    return {
        "issue": issue,
        "thread_id": thread_id,
        "customer_id": 7,
        "ticket_id": 9,
        "propose_ticket_update": False,
        "principal": {
            "subject": "agent",
            "role": "support_agent",
            "actor_id": 1,
        },
    }


def test_simple_sim_question_stays_on_deterministic_path_with_role_filter() -> None:
    async def scenario() -> None:
        retriever = RecordingRetriever()
        investigator = RecordingInvestigator()
        workflow = SupportWorkflow(
            retriever,
            ForbiddenGateway(),
            lambda: None,
            checkpointer=InMemorySaver(),
            investigator=investigator,
        )
        state = _state("How do I activate my SIM?", "simple-sim-001")
        state.update({"customer_id": None, "ticket_id": None})
        result = await workflow.graph.ainvoke(
            state,
            {"configurable": {"thread_id": "simple-sim-001"}},
        )
        assert result["complexity"] == "simple"
        assert investigator.calls == 0
        assert retriever.filters.access_roles == ["public", "support_agent"]

    asyncio.run(scenario())


def test_repeated_roaming_case_routes_to_investigation_and_back_to_resolution() -> None:
    async def scenario() -> None:
        investigator = RecordingInvestigator()
        workflow = SupportWorkflow(
            RecordingRetriever(),
            ForbiddenGateway(),
            lambda: None,
            checkpointer=InMemorySaver(),
            investigator=investigator,
        )
        result = await workflow.graph.ainvoke(
            _state(
                "Repeated roaming activation failures require policy and history review",
                "complex-roam-001",
            ),
            {"configurable": {"thread_id": "complex-roam-001"}},
        )
        assert result["complexity"] == "investigation"
        assert investigator.calls == 1
        assert result["resolution"]["evidence"][0]["source_id"] == "gateway-ticket-1"
        assert result["resolution"]["action_required"] is False

    asyncio.run(scenario())


def test_unavailable_investigation_fails_closed_without_controlled_action() -> None:
    async def scenario() -> None:
        workflow = SupportWorkflow(
            RecordingRetriever(),
            ForbiddenGateway(),
            lambda: None,
            checkpointer=InMemorySaver(),
            investigator=RecordingInvestigator(fail=True),
        )
        result = await workflow.graph.ainvoke(
            _state("Recurring billing records mismatch again", "complex-fail-001"),
            {"configurable": {"thread_id": "complex-fail-001"}},
        )
        assert "investigation_failed_safely" in result["errors"]
        assert result["resolution"]["insufficient_evidence"] is True
        assert result["resolution"]["ticket_draft"] is None

    asyncio.run(scenario())


def test_deep_agent_uses_official_factory_read_only_tools_and_strict_output(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict = {}

    class Agent:
        async def ainvoke(self, payload: dict, config: dict) -> dict:
            captured["payload"] = payload
            captured["config"] = config
            return {
                "structured_response": {
                    "issue_classification": "roaming",
                    "investigation_summary": "No evidence yet.",
                    "citations": [],
                    "findings": [],
                    "uncertainties": ["Tools were not needed by the fake model."],
                    "recommended_next_steps": ["Escalate."],
                    "status": "insufficient_evidence",
                }
            }

    def fake_factory(**kwargs: object) -> Agent:
        captured["factory"] = kwargs
        return Agent()

    monkeypatch.setattr(
        "backend.app.workflow.investigation.create_deep_agent", fake_factory
    )
    investigator = DeepAgentInvestigator(
        ForbiddenGateway(),
        model="test:bounded-model",
        openai_api_key=SecretStr("offline-test-key"),
        max_steps=4,
        max_tool_calls=3,
    )
    result = asyncio.run(
        investigator.investigate(
            issue="Repeated roaming problem for jane@example.test",
            issue_type="roaming",
            customer_id=7,
            ticket_id=9,
            principal=GatewayPrincipal(
                subject="agent", role="support_agent", actor_id=1
            ),
        )
    )
    names = {tool.name.replace("__", ".") for tool in captured["factory"]["tools"]}
    assert names <= READ_ONLY_TOOLS
    assert not any(
        "create" in name or "update" in name or "promote" in name for name in names
    )
    assert "jane@example.test" not in str(captured["payload"])
    assert result.status == "insufficient_evidence"


def test_invalid_deep_agent_structured_output_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class InvalidAgent:
        async def ainvoke(self, payload: dict, config: dict) -> dict:
            return {"structured_response": {"status": "completed"}}

    monkeypatch.setattr(
        "backend.app.workflow.investigation.create_deep_agent",
        lambda **kwargs: InvalidAgent(),
    )
    investigator = DeepAgentInvestigator(
        ForbiddenGateway(),
        model="test:invalid",
        openai_api_key=SecretStr("offline-test-key"),
    )
    with pytest.raises(InvestigationUnavailable):
        asyncio.run(
            investigator.investigate(
                issue="Repeated network outage history",
                issue_type="network",
                customer_id=None,
                ticket_id=9,
                principal=GatewayPrincipal(
                    subject="agent", role="support_agent", actor_id=1
                ),
            )
        )


def test_deep_agent_timeout_budget_fails_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class SlowAgent:
        async def ainvoke(self, payload: dict, config: dict) -> dict:
            await asyncio.sleep(0.1)
            return {}

    monkeypatch.setattr(
        "backend.app.workflow.investigation.create_deep_agent",
        lambda **kwargs: SlowAgent(),
    )
    investigator = DeepAgentInvestigator(
        ForbiddenGateway(),
        model="test:slow",
        openai_api_key=SecretStr("offline-test-key"),
        timeout_seconds=0.001,
    )
    with pytest.raises(InvestigationUnavailable):
        asyncio.run(
            investigator.investigate(
                issue="Repeated network incident history",
                issue_type="network",
                customer_id=None,
                ticket_id=9,
                principal=GatewayPrincipal(
                    subject="agent", role="support_agent", actor_id=1
                ),
            )
        )


def test_tool_allowlist_never_contains_controlled_writes() -> None:
    assert READ_ONLY_TOOLS.isdisjoint(
        {
            "ticket.create_ticket",
            "ticket.update_ticket",
            "knowledge.promote_knowledge",
        }
    )
