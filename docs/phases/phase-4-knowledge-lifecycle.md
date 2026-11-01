# Phase 4 — Knowledge Lifecycle Management

**Status:** DONE  
**Validated:** 2026-10-25

## Implementation

- PostgreSQL `knowledge_documents` stores stable UUID5 lineage roots.
- `knowledge_versions` stores immutable content/checksum/metadata, version
  labels, supersession links, lifecycle status, creator/promoter identity, and
  approval linkage.
- SHA-256 detects unchanged uploads and skips indexing work.
- Duplicate version labels with changed content fail with conflict.
- Draft uploads are inactive. Phase 9 promotion stages new Qdrant content as
  inactive, hides the prior point, commits PostgreSQL authority, and only then
  publishes the new point.
- Audit events record upload, unchanged detection, promotion denial/success,
  and deactivation without storing credentials.
- FastAPI endpoints validate strict Pydantic schemas and authenticate HS256
  bearer tokens using an environment-only secret.
- Authoritative promotion is enabled only through Phase 9 exact-scope approval,
  Gateway, and Knowledge MCP verification. Direct service construction remains
  fail-closed unless approval execution is explicitly enabled.

## Files

- `backend/app/models/knowledge_document.py`
- `backend/app/models/knowledge_version.py`
- `backend/alembic/versions/61f42e7c9a10_create_knowledge_lifecycle_tables.py`
- `backend/alembic/versions/c3e7a91d5f20_add_knowledge_promotion_state.py`
- `backend/app/services/knowledge_lifecycle.py`
- `backend/app/api/routes/knowledge_admin.py`
- `backend/app/schemas/knowledge_admin.py`

## Security and limitations

Inactive versions are excluded by the Qdrant `active=true` filter. The database
uniqueness constraints prevent duplicate document version/checksum pairs.
PostgreSQL and Qdrant cannot share one atomic transaction. The Phase 9
`staging/staged/committed/published` protocol makes every intermediate state
safe and retryable. It can temporarily return no current document during a
failure window, but it never exposes an unapproved draft or a superseded version
as current. Automatic background reconciliation remains a Phase 14 enhancement;
authorized same-request retry performs reconciliation today.
