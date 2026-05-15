"""
Test data for GitHub Dockerfiles module.

This module contains mock data that simulates GitHub's REST API responses
for code search and file content endpoints.
"""

import base64
from typing import Any

# Mock response from GitHub Code Search API (/search/code)
# when searching for "filename:dockerfile repo:owner/repo"
SEARCH_DOCKERFILES_RESPONSE: dict[str, Any] = {
    "total_count": 3,
    "incomplete_results": False,
    "items": [
        {
            "name": "Dockerfile",
            "path": "Dockerfile",
            "sha": "abc123def456",
            "url": "https://api.github.com/repos/testorg/testrepo/contents/Dockerfile?ref=main",
            "git_url": "https://api.github.com/repos/testorg/testrepo/git/blobs/abc123def456",
            "html_url": "https://github.com/testorg/testrepo/blob/main/Dockerfile",
            "repository": {
                "id": 123456789,
                "name": "testrepo",
                "full_name": "testorg/testrepo",
            },
            "score": 1.0,
        },
        {
            "name": "Dockerfile.dev",
            "path": "docker/Dockerfile.dev",
            "sha": "def789ghi012",
            "url": "https://api.github.com/repos/testorg/testrepo/contents/docker/Dockerfile.dev?ref=main",
            "git_url": "https://api.github.com/repos/testorg/testrepo/git/blobs/def789ghi012",
            "html_url": "https://github.com/testorg/testrepo/blob/main/docker/Dockerfile.dev",
            "repository": {
                "id": 123456789,
                "name": "testrepo",
                "full_name": "testorg/testrepo",
            },
            "score": 1.0,
        },
        {
            "name": "production.dockerfile",
            "path": "deploy/production.dockerfile",
            "sha": "ghi345jkl678",
            "url": "https://api.github.com/repos/testorg/testrepo/contents/deploy/production.dockerfile?ref=main",
            "git_url": "https://api.github.com/repos/testorg/testrepo/git/blobs/ghi345jkl678",
            "html_url": "https://github.com/testorg/testrepo/blob/main/deploy/production.dockerfile",
            "repository": {
                "id": 123456789,
                "name": "testrepo",
                "full_name": "testorg/testrepo",
            },
            "score": 1.0,
        },
    ],
}

# Empty search response (no Dockerfiles found)
SEARCH_DOCKERFILES_EMPTY_RESPONSE: dict[str, Any] = {
    "total_count": 0,
    "incomplete_results": False,
    "items": [],
}

# Mock response from GitHub Code Search API for org-wide search
# when searching for "filename:dockerfile org:testorg"
SEARCH_DOCKERFILES_ORG_RESPONSE: dict[str, Any] = {
    "total_count": 3,
    "incomplete_results": False,
    "items": [
        {
            "name": "Dockerfile",
            "path": "Dockerfile",
            "sha": "abc123def456",
            "url": "https://api.github.com/repos/testorg/testrepo/contents/Dockerfile?ref=main",
            "git_url": "https://api.github.com/repos/testorg/testrepo/git/blobs/abc123def456",
            "html_url": "https://github.com/testorg/testrepo/blob/main/Dockerfile",
            "repository": {
                "id": 123456789,
                "name": "testrepo",
                "full_name": "testorg/testrepo",
            },
            "score": 1.0,
        },
        {
            "name": "Dockerfile.dev",
            "path": "docker/Dockerfile.dev",
            "sha": "def789ghi012",
            "url": "https://api.github.com/repos/testorg/testrepo/contents/docker/Dockerfile.dev?ref=main",
            "git_url": "https://api.github.com/repos/testorg/testrepo/git/blobs/def789ghi012",
            "html_url": "https://github.com/testorg/testrepo/blob/main/docker/Dockerfile.dev",
            "repository": {
                "id": 123456789,
                "name": "testrepo",
                "full_name": "testorg/testrepo",
            },
            "score": 1.0,
        },
        {
            "name": "production.dockerfile",
            "path": "deploy/production.dockerfile",
            "sha": "ghi345jkl678",
            "url": "https://api.github.com/repos/testorg/testrepo/contents/deploy/production.dockerfile?ref=main",
            "git_url": "https://api.github.com/repos/testorg/testrepo/git/blobs/ghi345jkl678",
            "html_url": "https://github.com/testorg/testrepo/blob/main/deploy/production.dockerfile",
            "repository": {
                "id": 123456789,
                "name": "testrepo",
                "full_name": "testorg/testrepo",
            },
            "score": 1.0,
        },
    ],
}

# Mock Dockerfile content (base64 encoded as returned by GitHub Contents API)
DOCKERFILE_CONTENT = """FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8080

CMD ["python", "main.py"]
"""

DOCKERFILE_DEV_CONTENT = """FROM python:3.11

WORKDIR /app

# Install dev dependencies
RUN pip install pytest black flake8

COPY . .

CMD ["pytest"]
"""

DOCKERFILE_PROD_CONTENT = """FROM python:3.11-slim AS builder

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM python:3.11-slim
WORKDIR /app
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY . .

USER nobody
EXPOSE 8080
CMD ["gunicorn", "app:app"]
"""

# Mock response from GitHub Contents API (/repos/owner/repo/contents/path)
FILE_CONTENT_DOCKERFILE: dict[str, Any] = {
    "name": "Dockerfile",
    "path": "Dockerfile",
    "sha": "abc123def456",
    "size": len(DOCKERFILE_CONTENT),
    "url": "https://api.github.com/repos/testorg/testrepo/contents/Dockerfile?ref=main",
    "html_url": "https://github.com/testorg/testrepo/blob/main/Dockerfile",
    "git_url": "https://api.github.com/repos/testorg/testrepo/git/blobs/abc123def456",
    "download_url": "https://raw.githubusercontent.com/testorg/testrepo/main/Dockerfile",
    "type": "file",
    "content": base64.b64encode(DOCKERFILE_CONTENT.encode()).decode() + "\n",
    "encoding": "base64",
}

FILE_CONTENT_DOCKERFILE_DEV: dict[str, Any] = {
    "name": "Dockerfile.dev",
    "path": "docker/Dockerfile.dev",
    "sha": "def789ghi012",
    "size": len(DOCKERFILE_DEV_CONTENT),
    "url": "https://api.github.com/repos/testorg/testrepo/contents/docker/Dockerfile.dev?ref=main",
    "html_url": "https://github.com/testorg/testrepo/blob/main/docker/Dockerfile.dev",
    "git_url": "https://api.github.com/repos/testorg/testrepo/git/blobs/def789ghi012",
    "download_url": "https://raw.githubusercontent.com/testorg/testrepo/main/docker/Dockerfile.dev",
    "type": "file",
    "content": base64.b64encode(DOCKERFILE_DEV_CONTENT.encode()).decode() + "\n",
    "encoding": "base64",
}

FILE_CONTENT_DOCKERFILE_PROD: dict[str, Any] = {
    "name": "production.dockerfile",
    "path": "deploy/production.dockerfile",
    "sha": "ghi345jkl678",
    "size": len(DOCKERFILE_PROD_CONTENT),
    "url": "https://api.github.com/repos/testorg/testrepo/contents/deploy/production.dockerfile?ref=main",
    "html_url": "https://github.com/testorg/testrepo/blob/main/deploy/production.dockerfile",
    "git_url": "https://api.github.com/repos/testorg/testrepo/git/blobs/ghi345jkl678",
    "download_url": "https://raw.githubusercontent.com/testorg/testrepo/main/deploy/production.dockerfile",
    "type": "file",
    "content": base64.b64encode(DOCKERFILE_PROD_CONTENT.encode()).decode() + "\n",
    "encoding": "base64",
}

# Mock repository data (simplified version of what repos.py returns)
TEST_REPOS: list[dict[str, Any]] = [
    {
        "name": "testrepo",
        "nameWithOwner": "testorg/testrepo",
        "url": "https://github.com/testorg/testrepo",
        "owner": {
            "login": "testorg",
            "url": "https://github.com/testorg",
        },
    },
    {
        "name": "another-repo",
        "nameWithOwner": "testorg/another-repo",
        "url": "https://github.com/testorg/another-repo",
        "owner": {
            "login": "testorg",
            "url": "https://github.com/testorg",
        },
    },
]

# Expected output after sync
EXPECTED_DOCKERFILES_OUTPUT: list[dict[str, Any]] = [
    {
        "repo_url": "https://github.com/testorg/testrepo",
        "repo_name": "testorg/testrepo",
        "path": "Dockerfile",
        "content": DOCKERFILE_CONTENT,
        "sha": "abc123def456",
        "html_url": "https://github.com/testorg/testrepo/blob/main/Dockerfile",
    },
    {
        "repo_url": "https://github.com/testorg/testrepo",
        "repo_name": "testorg/testrepo",
        "path": "docker/Dockerfile.dev",
        "content": DOCKERFILE_DEV_CONTENT,
        "sha": "def789ghi012",
        "html_url": "https://github.com/testorg/testrepo/blob/main/docker/Dockerfile.dev",
    },
    {
        "repo_url": "https://github.com/testorg/testrepo",
        "repo_name": "testorg/testrepo",
        "path": "deploy/production.dockerfile",
        "content": DOCKERFILE_PROD_CONTENT,
        "sha": "ghi345jkl678",
        "html_url": "https://github.com/testorg/testrepo/blob/main/deploy/production.dockerfile",
    },
]
