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
        ({}, [{}], (None, None, None)),
        ({"permissions": {}}, [{}], ("none", "none", "none")),
        ({"permissions": {"contents": "write"}}, [{}], ("write", "none", "none")),
        (
            {"permissions": {"contents": "write"}},
            [{"permissions": {}}],
            ("none", "none", "none"),
        ),
        (
            {"permissions": {"contents": "write"}},
            [{"permissions": {"issues": "read"}}],
            ("none", "read", "none"),
        ),
        (
            {},
            [
                {"permissions": {"contents": "read"}},
                {"permissions": {"contents": "write", "id-token": "write"}},
            ],
            ("write", "none", "write"),
        ),
        (
            {"permissions": {"contents": "read"}},
            [{}, {"permissions": {"contents": "write", "id-token": "write"}}],
            ("write", "none", "write"),
        ),
        ({}, [{}, {"permissions": {"contents": "read"}}], (None, None, None)),
        ({}, [{}, {"permissions": {"contents": "write"}}], ("write", None, None)),
        ({}, [{"permissions": {}}, {"permissions": {}}], ("none", "none", "none")),
        (
            {"permissions": "write-all"},
            [{"permissions": "read-all"}],
            ("read", "read", "read"),
        ),
        (
            {"permissions": "read-all"},
            [{}, {"permissions": {"contents": "none"}}],
            ("read", "read", "read"),
        ),
        (
            {"permissions": {"contents": "write"}},
            [{"permissions": None}],
            (None, None, None),
        ),
        ({"permissions": "invalid"}, [{}], (None, None, None)),
        ({}, [{"permissions": ["write"]}], (None, None, None)),
        ({}, [{"permissions": {"contents": "invalid"}}], (None, None, None)),
        ({"permissions": {}}, [], ("none", "none", "none")),
        ({"permissions": {"contents": "read"}}, [], ("read", "none", "none")),
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
        assert (
            tuple(
                item[f"permissions_{scope}"]
                for scope in ("contents", "issues", "id_token")
            )
            == expected
        )
    assert all(item.permissions == parsed[0].permissions for item in parsed)


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
