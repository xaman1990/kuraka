---
name: generate-endpoint-tests
description: "Generate endpoint/API tests using FastAPI TestClient. Tests HTTP status codes, response shapes, auth requirements, and error formats."
agent: "[[test-engineer]]"
phase: "6 — see [[kuraka]]"
---

# Generate Endpoint Tests

Create endpoint tests that verify HTTP behavior using FastAPI TestClient.

## Input

- Endpoint file to test (e.g., `api/endpoints/tools/new_scale.py`)
- Test plan from [[analyze-testability]]

## Key Principle

Endpoint tests mock the **service layer** — they test HTTP handling, not business logic.

```
Endpoint Test → mocks → Service
                         ↓ (not tested here)
                     Repository → DB
```

## Test File Template

```python
"""Tests for New Scale endpoints."""

from io import BytesIO
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Test data builders
# ---------------------------------------------------------------------------

def _make_job_response(job_id: int = 1) -> dict:
    """Build a mock job for service return."""
    job = MagicMock()
    job.id = job_id
    job.tenant_id = 1
    job.name = "Test Job"
    job.company_id = 1
    job.status = "created"
    job.source_filename = "test.pdf"
    job.source_content_type = "application/pdf"
    job.provider_used = None
    job.error_message = None
    job.created_at = "2026-04-09T00:00:00Z"
    job.updated_at = "2026-04-09T00:00:00Z"
    job.company = MagicMock()
    job.company.name = "Asitur"
    return job


def _make_test_file() -> tuple[BytesIO, str]:
    """Create a fake PDF file for upload tests."""
    content = b"%PDF-1.4 fake content"
    return BytesIO(content), "test.pdf"


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestCreateJob:
    """POST /tools/new-scale/jobs"""

    @patch("api.endpoints.tools.new_scale.service")
    def test_should_return_200_when_valid_upload(
        self, mock_service, client, auth_headers,
    ):
        # Arrange
        mock_service.create_job.return_value = _make_job_response()
        file_content, filename = _make_test_file()

        # Act
        response = client.post(
            "/api/tools/new-scale/jobs",
            headers=auth_headers,
            files={"file": (filename, file_content, "application/pdf")},
            data={"name": "Test", "company_id": "1"},
        )

        # Assert
        assert response.status_code == 200
        mock_service.create_job.assert_called_once()

    def test_should_return_401_when_no_auth(self, client):
        # Act
        response = client.post("/api/tools/new-scale/jobs")

        # Assert
        assert response.status_code == 401


class TestListJobs:
    """GET /tools/new-scale/jobs"""

    @patch("api.endpoints.tools.new_scale.service")
    def test_should_return_paginated_list(
        self, mock_service, client, auth_headers,
    ):
        # Arrange
        mock_service.list_jobs.return_value = ([], 0)

        # Act
        response = client.get(
            "/api/tools/new-scale/jobs",
            headers=auth_headers,
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
```

## What to Test per Endpoint

| Method | Test Cases |
|--------|-----------|
| **POST** | 200 on success, 401 no auth, 400 missing fields, 404 not found |
| **GET list** | 200 with items, 200 empty list, pagination params passed |
| **GET detail** | 200 found, 404 not found, tenant isolation |
| **PUT** | 200 updated, 404 not found, 400 invalid data |
| **DELETE** | 204 deleted, 404 not found |
| **Download** | 200 with streaming response, correct headers |

## Auth Testing

```python
def test_should_return_401_without_token(self, client):
    response = client.get("/api/tools/new-scale/jobs")
    assert response.status_code == 401

def test_should_return_403_wrong_role(self, client):
    # Use headers with non-tools role
    headers = {"Authorization": "Bearer viewer-token"}
    response = client.get("/api/tools/new-scale/jobs", headers=headers)
    assert response.status_code in (401, 403)
```

## Response Shape Testing

```python
def test_response_has_required_fields(self, client, auth_headers):
    with patch("...service") as mock:
        mock.list_jobs.return_value = ([mock_job], 1)
        response = client.get("/api/tools/new-scale/jobs", headers=auth_headers)
        
        data = response.json()
        item = data["items"][0]
        assert "id" in item
        assert "company_id" in item
        assert "status" in item
        assert "created_at" in item
```

## File Upload Testing

```python
def test_upload_sends_bytes_to_service(self, client, auth_headers):
    with patch("...service") as mock:
        mock.create_job.return_value = mock_job
        
        response = client.post(
            "/api/tools/new-scale/jobs",
            headers=auth_headers,
            files={"file": ("test.pdf", b"content", "application/pdf")},
            data={"name": "Test", "company_id": "1"},
        )
        
        # Verify service received the bytes
        call_args = mock.create_job.call_args
        assert call_args.args[4] == "test.pdf"  # filename
        assert isinstance(call_args.args[6], bytes)  # file_bytes
```

## Download Testing

```python
def test_download_returns_xlsx_content_type(self, client, auth_headers):
    with patch("...service") as mock:
        mock.download_excel.return_value = (BytesIO(b"xlsx"), "test.xlsx")
        
        response = client.get(
            "/api/tools/new-scale/jobs/1/download",
            headers=auth_headers,
        )
        
        assert response.status_code == 200
        assert "spreadsheetml" in response.headers["content-type"]
        assert "test.xlsx" in response.headers["content-disposition"]
```
