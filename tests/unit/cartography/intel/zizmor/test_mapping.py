"""
Unit tests for the Zizmor repository mapping file.
"""

from pathlib import Path

import pytest

from cartography.intel.common.object_store import LocalReportReader
from cartography.intel.zizmor.mapping import get_zizmor_repository_mappings


def test_get_zizmor_repository_mappings_happy_path():
    mapping_path = Path("tests/data/zizmor/repository_mappings.yaml")

    repository_mappings = get_zizmor_repository_mappings(
        LocalReportReader(str(mapping_path))
    )

    assert len(repository_mappings) == 2

    first_mapping = repository_mappings[0]
    assert first_mapping.repository_name == "simpsoncorp/sample_repo"
    assert first_mapping.repository_context == {
        "owner": "simpsoncorp",
        "repo": "sample_repo",
        "repositoryName": "simpsoncorp/sample_repo",
        "repositoryUrl": "https://github.com/simpsoncorp/sample_repo",
        "branch": "main",
    }
    assert first_mapping.reports == ["tests/data/zizmor/zizmor_report.json"]

    second_mapping = repository_mappings[1]
    assert second_mapping.repository_name == "different-org/different-repo"
    assert len(second_mapping.reports) == 2


def test_get_zizmor_repository_mappings_rejects_multiple_yaml_files():
    fixture_path = Path("tests/data/zizmor/repository_mappings_multiple_yaml")
    with pytest.raises(
        ValueError,
        match="Zizmor repository mapping source must contain exactly one YAML file.",
    ):
        get_zizmor_repository_mappings(LocalReportReader(str(fixture_path)))


def test_get_zizmor_repository_mappings_rejects_missing_required_fields():
    fixture_path = Path("tests/data/zizmor/repository_mappings_missing_fields.yaml")
    with pytest.raises(
        ValueError,
        match="Zizmor repository mapping file is invalid",
    ):
        get_zizmor_repository_mappings(LocalReportReader(str(fixture_path)))


def test_get_zizmor_repository_mappings_rejects_duplicate_repository_urls():
    """
    Cleanup is authorized per entry but scoped by repository URL, so a second
    entry for a repository could fail without withdrawing the authorization the
    first one granted. Findings are also keyed without the branch, so duplicate
    entries collide on the same nodes.
    """
    fixture_path = Path("tests/data/zizmor/repository_mappings_duplicate_url.yaml")
    with pytest.raises(
        ValueError,
        match="Each repository may only appear once",
    ):
        get_zizmor_repository_mappings(LocalReportReader(str(fixture_path)))


def test_get_zizmor_repository_mappings_rejects_duplicate_urls_differing_by_case():
    """GitHub repository names are unique without regard to case."""
    fixture_path = Path("tests/data/zizmor/repository_mappings_duplicate_url_case.yaml")
    with pytest.raises(
        ValueError,
        match="Each repository may only appear once",
    ):
        get_zizmor_repository_mappings(LocalReportReader(str(fixture_path)))


def test_get_zizmor_repository_mappings_rejects_empty_reports():
    fixture_path = Path("tests/data/zizmor/repository_mappings_empty_reports.yaml")
    with pytest.raises(
        ValueError,
        match="Zizmor repository mapping file is invalid",
    ):
        get_zizmor_repository_mappings(LocalReportReader(str(fixture_path)))
