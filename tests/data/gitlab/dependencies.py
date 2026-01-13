"""Test data for GitLab dependencies module."""

# Parsed CycloneDX SBOM dependencies (after parsing)
GET_GITLAB_DEPENDENCIES_RESPONSE = [
    {
        "name": "express",
        "version": "4.18.2",
        "package_manager": "npm",
        "manifest_path": "package.json",
        "manifest_id": "https://gitlab.example.com/myorg/awesome-project/blob/package.json",
    },
    {
        "name": "lodash",
        "version": "4.17.21",
        "package_manager": "npm",
        "manifest_path": "package.json",
        "manifest_id": "https://gitlab.example.com/myorg/awesome-project/blob/package.json",
    },
    {
        "name": "requests",
        "version": "2.31.0",
        "package_manager": "pypi",
        "manifest_path": "backend/requirements.txt",
    },
    {
        "name": "gin",
        "version": "1.9.1",
        "package_manager": "golang",
        "manifest_path": "services/api/go.mod",
    },
]

TEST_PROJECT_URL = "https://gitlab.example.com/myorg/awesome-project"

# Expected transformed dependencies output
TRANSFORMED_DEPENDENCIES = [
    {
        "id": "https://gitlab.example.com/myorg/awesome-project:npm:express@4.18.2",
        "name": "express",
        "version": "4.18.2",
        "package_manager": "npm",
        "project_url": TEST_PROJECT_URL,
        "manifest_id": "https://gitlab.example.com/myorg/awesome-project/blob/package.json",
    },
    {
        "id": "https://gitlab.example.com/myorg/awesome-project:npm:lodash@4.17.21",
        "name": "lodash",
        "version": "4.17.21",
        "package_manager": "npm",
        "project_url": TEST_PROJECT_URL,
        "manifest_id": "https://gitlab.example.com/myorg/awesome-project/blob/package.json",
    },
    {
        "id": "https://gitlab.example.com/myorg/awesome-project:pypi:requests@2.31.0",
        "name": "requests",
        "version": "2.31.0",
        "package_manager": "pypi",
        "project_url": TEST_PROJECT_URL,
    },
    {
        "id": "https://gitlab.example.com/myorg/awesome-project:golang:gin@1.9.1",
        "name": "gin",
        "version": "1.9.1",
        "package_manager": "golang",
        "project_url": TEST_PROJECT_URL,
    },
]
