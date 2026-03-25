"""Test data for GitLab dependencies module."""

# Parsed CycloneDX SBOM dependencies (after parsing)
GET_GITLAB_DEPENDENCIES_RESPONSE = [
    {
        "name": "express",
        "version": "4.18.2",
        "package_manager": "npm",
        "manifest_path": "package.json",
        "manifest_id": "https://gitlab.example.com/myorg/awesome-project/blob/package.json",
        "purl": "pkg:npm/express@4.18.2",
    },
    {
        "name": "lodash",
        "version": "4.17.21",
        "package_manager": "npm",
        "manifest_path": "package.json",
        "manifest_id": "https://gitlab.example.com/myorg/awesome-project/blob/package.json",
        "purl": "pkg:npm/lodash@4.17.21",
    },
    {
        "name": "requests",
        "version": "2.31.0",
        "package_manager": "pypi",
        "manifest_path": "backend/requirements.txt",
        "purl": "pkg:pypi/requests@2.31.0",
    },
    {
        "name": "gin",
        "version": "1.9.1",
        "package_manager": "golang",
        "manifest_path": "services/api/go.mod",
        "purl": "pkg:golang/gin@1.9.1",
    },
]

TEST_PROJECT_URL = "https://gitlab.example.com/myorg/awesome-project"

# Requirements parsed from manifest files
TEST_REQUIREMENTS_BY_MANIFEST = {
    "package.json": {
        "express": "^4.18.0",
        "lodash": "~4.17.0",
    },
    "backend/requirements.txt": {
        "requests": ">=2.31.0,<3.0",
    },
    "services/api/go.mod": {
        "gin": "v1.9.1",
    },
}

# Expected transformed dependencies output
TRANSFORMED_DEPENDENCIES = [
    {
        "id": "https://gitlab.example.com/myorg/awesome-project:npm:express@4.18.2",
        "name": "express",
        "original_name": "express",
        "version": "4.18.2",
        "requirements": "^4.18.0",
        "ecosystem": "npm",
        "package_manager": "npm",
        "manifest_file": "package.json",
        "purl": "pkg:npm/express@4.18.2",
        "type": "npm",
        "normalized_id": "npm|express|4.18.2",
        "project_url": TEST_PROJECT_URL,
        "manifest_id": "https://gitlab.example.com/myorg/awesome-project/blob/package.json",
    },
    {
        "id": "https://gitlab.example.com/myorg/awesome-project:npm:lodash@4.17.21",
        "name": "lodash",
        "original_name": "lodash",
        "version": "4.17.21",
        "requirements": "~4.17.0",
        "ecosystem": "npm",
        "package_manager": "npm",
        "manifest_file": "package.json",
        "purl": "pkg:npm/lodash@4.17.21",
        "type": "npm",
        "normalized_id": "npm|lodash|4.17.21",
        "project_url": TEST_PROJECT_URL,
        "manifest_id": "https://gitlab.example.com/myorg/awesome-project/blob/package.json",
    },
    {
        "id": "https://gitlab.example.com/myorg/awesome-project:pypi:requests@2.31.0",
        "name": "requests",
        "original_name": "requests",
        "version": "2.31.0",
        "requirements": ">=2.31.0,<3.0",
        "ecosystem": "pypi",
        "package_manager": "pypi",
        "manifest_file": "requirements.txt",
        "purl": "pkg:pypi/requests@2.31.0",
        "type": "pypi",
        "normalized_id": "pypi|requests|2.31.0",
        "project_url": TEST_PROJECT_URL,
    },
    {
        "id": "https://gitlab.example.com/myorg/awesome-project:golang:gin@1.9.1",
        "name": "gin",
        "original_name": "gin",
        "version": "1.9.1",
        "requirements": "v1.9.1",
        "ecosystem": "golang",
        "package_manager": "golang",
        "manifest_file": "go.mod",
        "purl": "pkg:golang/gin@1.9.1",
        "type": "golang",
        "normalized_id": "golang|gin|1.9.1",
        "project_url": TEST_PROJECT_URL,
    },
]
