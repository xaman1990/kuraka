---
name: generate-unit-tests
description: "Generate unit tests for services, repositories, and models. Uses pytest + AAA pattern, mocks dependencies, follows project naming conventions."
agent: "[[test-engineer]]"
phase: "6 — see `kuraka`"
---

# Generate Unit Tests

Create unit tests from a test plan produced by [[analyze-testability]].

## Input

- Test plan (from analyze-testability)
- Source file to test

## Test File Template

```python
"""Tests for {module_name}."""

from unittest.mock import MagicMock, patch

import pytest

# Import the module under test
from api.services.tools.new_scale import service

# Import types for test data builders
from api.models.tools.new_scale.enums import NewScaleJobStatus


# ---------------------------------------------------------------------------
# Test data builders
# ---------------------------------------------------------------------------

def _make_mock_job(
    job_id: int = 1,
    tenant_id: int = 1,
    status: str = NewScaleJobStatus.CREATED,
) -> MagicMock:
    """Build a mock NewScaleJob."""
    job = MagicMock()
    job.id = job_id
    job.tenant_id = tenant_id
    job.name = "Test Job"
    job.company_id = 1
    job.status = status
    job.company = MagicMock(name="Asitur")
    return job


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestCreateJob:
    """Tests for service.create_job()."""

    @patch("api.services.tools.new_scale.service.source_file_repository")
    @patch("api.services.tools.new_scale.service.job_repository")
    def test_should_create_job_when_valid_data(
        self, mock_job_repo, mock_file_repo,
    ):
        # Arrange
        mock_db = MagicMock()
        mock_job = _make_mock_job()
        mock_job_repo.create.return_value = mock_job

        # Act
        result = service.create_job(
            mock_db, tenant_id=1, name="Test", company_id=1,
            filename="test.pdf", content_type="application/pdf",
            file_bytes=b"fake-content",
        )

        # Assert
        assert result.id == 1
        mock_job_repo.create.assert_called_once()
        mock_file_repo.create.assert_called_once()
```

## Rules for Service Tests

1. **Mock all repositories** — services never touch real DB in unit tests
2. **Mock other services** — test in isolation
3. **Test state transitions** — verify status changes (CREATED → ANALYZING → etc.)
4. **Test validation** — verify ErrValidation raised for invalid states
5. **Test not-found** — verify ErrNotFound raised when entity missing
6. **Return value assertions** — verify the function returns expected data

## Rules for Repository Tests

1. **Use `db_session` fixture** — real DB with auto-rollback
2. **Create test data in Arrange** — insert via `db_session.add()`
3. **Test CRUD** — create, read, update, list, delete
4. **Test tenant isolation** — same ID different tenant → not found
5. **Test pagination** — verify offset/limit behavior
6. **Test constraints** — unique violations, FK constraints

```python
class TestJobRepository:
    def test_should_create_job(self, db_session, test_tenant):
        # Arrange
        from repositories.tools.new_scale import job_repository
        
        # Act
        job = job_repository.create(
            db_session,
            tenant_id=test_tenant["id"],
            name="Test",
            company_id=1,
            status="created",
            source_filename="test.pdf",
            source_content_type="application/pdf",
        )
        
        # Assert
        assert job.id is not None
        assert job.tenant_id == test_tenant["id"]
```

## Rules for Model Tests

1. **No DB queries** — test `__table__` metadata only
2. **Verify columns exist** — `assert "column" in Model.__table__.columns`
3. **Verify FK targets** — check `foreign_keys` set
4. **Verify constraints** — unique, check, not-null
5. **Verify relationships** — if defined

## After Writing

1. Run `ruff check` on the test file
2. Run `make test-one T=test_name` to verify individual test
3. Run `make test` to verify full suite still passes
