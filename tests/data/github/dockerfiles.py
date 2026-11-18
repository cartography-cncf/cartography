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


# Two organizations synced in one run. The demo organization's short Dockerfile
# copies the same final layer as the platform service, so Dockerfile similarity
# alone cannot tell them apart; the image's OCI source label can.
DEMO_ORG_REPOS: list[dict[str, Any]] = [
    {
        "url": "https://github.com/example-demos/node-starter",
        "name": "node-starter",
        "owner": {"login": "example-demos"},
    },
]

PLATFORM_ORG_REPOS: list[dict[str, Any]] = [
    {
        "url": "https://github.com/example-platform/api",
        "name": "api",
        "owner": {"login": "example-platform"},
    },
]

DEMO_DOCKERFILE_CONTENT = """FROM node:20-slim
COPY . /app
CMD ["node", "server.js"]
"""

PLATFORM_DOCKERFILE_CONTENT = """FROM node:20-slim
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --omit=dev
COPY . /app
CMD ["node", "server.js"]
"""


def _search_response(org: str, repo: str, repo_id: int) -> dict[str, Any]:
    return {
        "total_count": 1,
        "incomplete_results": False,
        "items": [
            {
                "name": "Dockerfile",
                "path": "Dockerfile",
                "sha": f"{repo}-dockerfile-sha",
                "url": f"https://api.github.com/repos/{org}/{repo}/contents/Dockerfile?ref=main",
                "git_url": f"https://api.github.com/repos/{org}/{repo}/git/blobs/{repo}-dockerfile-sha",
                "html_url": f"https://github.com/{org}/{repo}/blob/main/Dockerfile",
                "repository": {
                    "id": repo_id,
                    "name": repo,
                    "full_name": f"{org}/{repo}",
                },
                "score": 1.0,
            },
        ],
    }


def _file_content_response(content: str) -> dict[str, Any]:
    return {
        "type": "file",
        "encoding": "base64",
        "name": "Dockerfile",
        "path": "Dockerfile",
        "content": base64.b64encode(content.encode("utf-8")).decode("utf-8"),
    }


MULTI_ORG_REST_RESPONSES: dict[str, dict[str, Any]] = {
    "org:example-demos": _search_response("example-demos", "node-starter", 700000001),
    "org:example-platform": _search_response("example-platform", "api", 700000002),
    "/repos/example-demos/node-starter/contents/Dockerfile": _file_content_response(
        DEMO_DOCKERFILE_CONTENT,
    ),
    "/repos/example-platform/api/contents/Dockerfile": _file_content_response(
        PLATFORM_DOCKERFILE_CONTENT,
    ),
}

# BuildKit history for an image built from PLATFORM_DOCKERFILE_CONTENT.
PLATFORM_IMAGE_LAYER_HISTORY: list[str] = [
    "# debian.sh --arch 'amd64' out/ 'bookworm' '@1730073600'",
    "ENV NODE_VERSION=20.18.0",
    'RUN /bin/sh -c set -ex && ARCH= && dpkgArch="$(dpkg --print-architecture)" # buildkit',
    "WORKDIR /app",
    "COPY package.json package-lock.json ./ # buildkit",
    "RUN /bin/sh -c npm ci --omit=dev # buildkit",
    "COPY . /app # buildkit",
]
