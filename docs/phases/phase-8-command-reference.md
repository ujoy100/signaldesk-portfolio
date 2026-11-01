# Phase 8 command reference

```bash
.venv/bin/pytest backend/tests/test_support_schemas.py backend/tests/test_support_workflow.py -q
.venv/bin/ruff format --check backend
.venv/bin/ruff check backend
```

Production model selection and credentials must remain external when an
LLM-backed generator is introduced.
