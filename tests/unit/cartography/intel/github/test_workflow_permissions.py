"""Declared workflow permissions must be independent of job ordering."""

from itertools import permutations

import pytest
import yaml

from cartography.intel.github.actions import enrich_workflow_with_parsed_content
from cartography.intel.github.workflow_parser import ALL_PERMISSION_SCOPES
from cartography.intel.github.workflow_parser import parse_workflow_yaml


@pytest.mark.parametrize(
    "defaults,jobs,expected",
    [
        pytest.param(
            {},
            [{}],
            {"contents": None, "issues": None, "id_token": None},
            id="omitted defaults remain unknown",
        ),
        pytest.param(
            {"permissions": {}},
            [{}],
            {"contents": "none", "issues": "none", "id_token": "none"},
            id="empty workflow block denies all scopes",
        ),
        pytest.param(
            {"permissions": {"contents": "write"}},
            [{}],
            {"contents": "write", "issues": "none", "id_token": "none"},
            id="job inherits workflow default",
        ),
        pytest.param(
            {"permissions": {"contents": "write"}},
            [{"permissions": {}}],
            {"contents": "none", "issues": "none", "id_token": "none"},
            id="empty job block replaces workflow default",
        ),
        pytest.param(
            {"permissions": {"contents": "write"}},
            [{"permissions": {"issues": "read"}}],
            {"contents": "none", "issues": "read", "id_token": "none"},
            id="job block replaces workflow default",
        ),
        pytest.param(
            {},
            [
                {"permissions": {"contents": "read"}},
                {"permissions": {"contents": "write", "id-token": "write"}},
            ],
            {"contents": "write", "issues": "none", "id_token": "write"},
            id="explicit writes survive job ordering",
        ),
        pytest.param(
            {"permissions": {"contents": "read"}},
            [{}, {"permissions": {"contents": "write", "id-token": "write"}}],
            {"contents": "write", "issues": "none", "id_token": "write"},
            id="explicit write overrides inherited read",
        ),
        pytest.param(
            {},
            [{}, {"permissions": {"contents": "read"}}],
            {"contents": None, "issues": None, "id_token": None},
            id="unknown job prevents read conclusion",
        ),
        pytest.param(
            {},
            [{}, {"permissions": {"contents": "write"}}],
            {"contents": "write", "issues": None, "id_token": None},
            id="known write survives unknown job",
        ),
        pytest.param(
            {},
            [{"permissions": {}}, {"permissions": {}}],
            {"contents": "none", "issues": "none", "id_token": "none"},
            id="all empty job blocks deny access",
        ),
        pytest.param(
            {"permissions": "write-all"},
            [{"permissions": "read-all"}],
            {"contents": "read", "issues": "read", "id_token": "none"},
            id="job read-all replaces workflow write-all",
        ),
        pytest.param(
            {"permissions": "read-all"},
            [{}, {"permissions": {"contents": "none"}}],
            {"contents": "read", "issues": "read", "id_token": "none"},
            id="job denial coexists with inherited read-all",
        ),
        pytest.param(
            {"permissions": {"contents": "write"}},
            [{"permissions": None}],
            {"contents": None, "issues": None, "id_token": None},
            id="null job block does not inherit",
        ),
        pytest.param(
            {"permissions": "read-all"},
            [{}],
            {"contents": "read", "issues": "read", "id_token": "none"},
            id="read-all denies id-token",
        ),
        pytest.param(
            {"permissions": {"id-token": "read"}},
            [{}],
            {"contents": None, "issues": None, "id_token": None},
            id="invalid workflow id-token read stays unknown",
        ),
        pytest.param(
            {},
            [{"permissions": {"id-token": "read"}}],
            {"contents": None, "issues": None, "id_token": None},
            id="invalid job id-token read stays unknown",
        ),
        pytest.param(
            {},
            [
                {"permissions": {"id-token": "write"}},
                {"permissions": {"id-token": "read"}},
            ],
            {"contents": None, "issues": None, "id_token": "write"},
            id="known id-token write survives invalid job",
        ),
        pytest.param(
            {"permissions": "invalid"},
            [{}],
            {"contents": None, "issues": None, "id_token": None},
            id="invalid workflow scalar stays unknown",
        ),
        pytest.param(
            {},
            [{"permissions": ["write"]}],
            {"contents": None, "issues": None, "id_token": None},
            id="invalid job list stays unknown",
        ),
        pytest.param(
            {},
            [{"permissions": {"contents": "invalid"}}],
            {"contents": None, "issues": None, "id_token": None},
            id="invalid permission level stays unknown",
        ),
        pytest.param(
            {"permissions": {}},
            [],
            {"contents": "none", "issues": "none", "id_token": "none"},
            id="no jobs retains empty workflow block",
        ),
        pytest.param(
            {"permissions": {"contents": "read"}},
            [],
            {"contents": "read", "issues": "none", "id_token": "none"},
            id="no jobs retains workflow declaration",
        ),
    ],
)
def test_permission_summary_defaults_overrides_and_order(defaults, jobs, expected):
    # Arrange: each permutation represents the same declared jobs.
    workflows = [
        yaml.safe_dump(
            {**defaults, "jobs": {f"job{i}": job for i, job in order}}, sort_keys=False
        )
        for order in permutations(enumerate(jobs))
    ]

    # Act
    parsed = [parse_workflow_yaml(content) for content in workflows]
    enriched = [
        enrich_workflow_with_parsed_content({}, item, "org", "repo") for item in parsed
    ]

    # Assert
    for item in enriched:
        assert {scope: item[f"permissions_{scope}"] for scope in expected} == expected
    assert all(item.permissions == parsed[0].permissions for item in parsed)


def test_sphinx_build_read_and_deploy_write_summary():
    # Arrange: Cartography's sphinx.yml used this permission layout.
    content = """permissions: read-all
jobs:
  build:
    runs-on: ubuntu-latest
    permissions:
      contents: read
    steps:
      - run: echo build
  deploy:
    runs-on: ubuntu-latest
    permissions:
      contents: write
    steps:
      - run: echo deploy
"""

    # Act
    parsed = parse_workflow_yaml(content)

    # Assert: the old parser kept the first job's read and missed deploy's write.
    assert parsed.permissions["contents"] == "write"


def test_reusable_workflow_records_only_caller_declarations():
    # Arrange
    content = """jobs:
  call:
    uses: example/repo/.github/workflows/reuse.yml@main
    permissions:
      contents: write
"""

    # Act
    parsed = parse_workflow_yaml(content)

    # Assert
    assert parsed.permissions["contents"] == "write"
    assert parsed.permissions["issues"] == "none"
    assert len(parsed.reusable_workflow_calls) == 1


@pytest.mark.parametrize("content", ["", "[", "42"])
def test_missing_or_invalid_content_remains_unknown(content):
    # Arrange
    parsed = parse_workflow_yaml(content)

    # Act
    enriched = enrich_workflow_with_parsed_content({}, parsed, "org", "repo")

    # Assert
    assert all(
        enriched[f"permissions_{scope}"] is None for scope in ALL_PERMISSION_SCOPES
    )


@pytest.mark.parametrize("jobs", [None, [], {"invalid": "not a job mapping"}])
def test_invalid_jobs_preserve_explicit_workflow_declarations(jobs):
    # Arrange
    content = yaml.safe_dump({"permissions": {"contents": "read"}, "jobs": jobs})

    # Act
    parsed = parse_workflow_yaml(content)

    # Assert
    assert parsed.permissions["contents"] == "read"
    assert parsed.permissions["issues"] == "none"


def test_invalid_permission_scope_is_unknown():
    # Arrange
    content = yaml.safe_dump({"jobs": {"check": {"permissions": {1: "write"}}}})

    # Act
    parsed = parse_workflow_yaml(content)

    # Assert
    assert parsed.permissions == {}
