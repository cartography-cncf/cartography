"""
Unit tests for Semgrep dependency helpers.
"""

from cartography.intel.semgrep.dependencies import transform_dependencies


def _raw_dep(url: str) -> dict:
    return {
        "repositoryId": "123456",
        "definedAt": {
            "path": "go.mod",
            "startLine": "6",
            "endLine": "6",
            "url": url,
            "committedAt": "1970-01-01T00:00:00Z",
            "startCol": "0",
            "endCol": "0",
        },
        "transitivity": "DIRECT",
        "package": {"name": "github.com/foo/bar", "versionSpecifier": "1.2.3"},
        "ecosystem": "gomod",
        "licenses": [],
        "pathToTransitivity": [],
    }


def test_transform_dependencies_extracts_github_repo_url():
    raw_deps = [
        _raw_dep(
            "https://github.com/simpsoncorp/sample_repo/blob/00000000000000000000000000000000/go.mod#L6"
        ),
    ]

    deps = transform_dependencies(raw_deps)

    assert deps[0]["repo_url"] == "https://github.com/simpsoncorp/sample_repo"


def test_transform_dependencies_extracts_gitlab_project_url():
    # GitLab blob URLs include `/-/` between the project path and `blob`.
    raw_deps = [
        _raw_dep(
            "https://gitlab.com/simpsoncorp/sample_repo/-/blob/00000000000000000000000000000000/go.mod#L6"
        ),
    ]

    deps = transform_dependencies(raw_deps)

    assert deps[0]["repo_url"] == "https://gitlab.com/simpsoncorp/sample_repo"
