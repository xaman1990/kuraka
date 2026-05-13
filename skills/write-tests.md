---
name: write-tests
description: "Write unit and integration tests for implemented functionality. Uses pytest with AAA pattern. Used in Phase 6 of the workflow."
agent: "[[backend-developer]]"
phase: "6 — see `kuraka`"
---

# Write Tests

You are executing the Test Writing skill (Phase 6 of the workflow).

## Input

Implemented code from Phase 4/5. Review story files for required test cases.

## Steps

### 1. Identify What Needs Tests

For each implemented file, determine test needs:

| Source File | Test File | Type |
|-------------|-----------|------|
| `api/services/{module}/service.py` | `tests/unit/services/test_{service}.py` | Unit |
| `repositories/{module}/repo.py` | `tests/unit/repositories/test_{repo}.py` | Unit |
| `api/endpoints/{module}/endpoint.py` | `tests/integration/test_{endpoint}.py` | Integration |

### 2. Test Structure

```python
"""Tests for {module} {layer}."""
import pytest
from unittest.mock import MagicMock, AsyncMock, patch

# Fixtures in conftest.py, not here


class TestServiceMethod:
    """Tests for ServiceClass.method_name."""

    def test_should_return_result_when_valid_input(self):
        """Happy path."""
        # Arrange
        mock_repo = MagicMock()
        mock_repo.find_by_id.return_value = expected_entity
        service = ServiceClass(mock_repo)

        # Act
        result = service.get_by_id(1)

        # Assert
        assert result.id == 1
        mock_repo.find_by_id.assert_called_once_with(1)

    def test_should_raise_not_found_when_id_missing(self):
        """Error case: entity not found."""
        # Arrange
        mock_repo = MagicMock()
        mock_repo.find_by_id.return_value = None
        service = ServiceClass(mock_repo)

        # Act & Assert
        with pytest.raises(ErrNotFound):
            service.get_by_id(999)

    def test_should_return_empty_list_when_no_records(self):
        """Edge case: no data."""
        # Arrange
        mock_repo = MagicMock()
        mock_repo.find_all.return_value = []
        service = ServiceClass(mock_repo)

        # Act
        result = service.get_all()

        # Assert
        assert result == []
```

### 3. What to Test

**MUST test:**
- Happy path (valid input -> expected output)
- Error cases (not found, validation failure, auth denied)
- Edge cases (empty list, null values, zero, boundary values)
- Business logic transformations
- Tenant isolation (ensure queries include tenant_id)

**DON'T test:**
- Framework internals (FastAPI, SQLAlchemy)
- Simple getters/setters
- Config files
- Third-party libraries

### 4. Mocking Rules

- **Unit tests**: Mock repositories when testing services, mock DB when testing repositories
- **Integration tests**: Use TestClient with test DB
- **Never mock**: The code under test itself
- **Always mock**: External APIs, email, file system

### 5. Run Tests

```bash
cd sie_v2 && make test
```

Verify:
- All tests pass
- No warnings about unclosed resources
- `ruff check .` still passes

### 6. Report

- Tests created (count and files)
- All passing? Yes/No
- Coverage notes (what's covered, what's not)
