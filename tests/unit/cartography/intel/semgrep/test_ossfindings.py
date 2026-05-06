"""
Unit tests for Semgrep OSS findings helpers.
"""

from pathlib import Path

import pytest

from cartography.intel.common.object_store import LocalReportReader
from cartography.intel.semgrep.ossfindings import _build_oss_sast_finding_id
from cartography.intel.semgrep.ossfindings import get_semgrep_oss_report
from cartography.intel.semgrep.ossfindings import (
    get_semgrep_oss_reports_for_repository_mapping,
)
from cartography.intel.semgrep.ossfindings import get_semgrep_oss_repository_mappings


def test_get_semgrep_oss_repository_mappings_happy_path():
    mapping_path = Path("tests/data/semgrep/repository_mappings.yaml")

    repository_mappings = get_semgrep_oss_repository_mappings(
        LocalReportReader(str(mapping_path))
    )

    assert len(repository_mappings) == 2

    first_mapping = repository_mappings[0]
    assert first_mapping.repository_name == "simpsoncorp/sample_repo"
    assert first_mapping.repository_context == {
        "repositoryName": "simpsoncorp/sample_repo",
        "repositoryUrl": "https://github.com/simpsoncorp/sample_repo",
        "branch": "main",
    }
    assert first_mapping.reports == ["tests/data/semgrep/oss_sast_report.json"]

    second_mapping = repository_mappings[1]
    assert second_mapping.repository_name == "different-org/different-repo"
    assert len(second_mapping.reports) == 2


def test_get_semgrep_oss_reports_for_repository_mapping_happy_path():
    mapping_path = Path("tests/data/semgrep/repository_mappings.yaml")
    repository_mapping = get_semgrep_oss_repository_mappings(
        LocalReportReader(str(mapping_path))
    )[0]

    report_collection = get_semgrep_oss_reports_for_repository_mapping(
        repository_mapping
    )

    assert report_collection.repository_mapping == repository_mapping
    assert report_collection.total_sources == 1
    assert report_collection.successful_sources == 1
    assert report_collection.failed_sources == 0
    assert report_collection.all_sources_succeeded is True
    assert report_collection.any_reports_processed is True
    assert len(report_collection.reports) == 1
    assert report_collection.reports[0][0].name == "oss_sast_report.json"
    assert isinstance(report_collection.reports[0][1]["results"], list)


def test_get_semgrep_oss_repository_mappings_rejects_multiple_yaml_files():
    fixture_path = Path("tests/data/semgrep/repository_mappings_multiple_yaml")
    with pytest.raises(
        ValueError,
        match="Semgrep OSS repository mapping source must contain exactly one YAML file.",
    ):
        get_semgrep_oss_repository_mappings(LocalReportReader(str(fixture_path)))


def test_get_semgrep_oss_repository_mappings_rejects_missing_required_fields():
    fixture_path = Path("tests/data/semgrep/repository_mappings_missing_fields.yaml")
    with pytest.raises(
        ValueError,
        match="Semgrep OSS repository mapping file is invalid",
    ):
        get_semgrep_oss_repository_mappings(LocalReportReader(str(fixture_path)))


def test_get_semgrep_oss_repository_mappings_rejects_empty_reports():
    fixture_path = Path("tests/data/semgrep/repository_mappings_empty_reports.yaml")
    with pytest.raises(
        ValueError,
        match="Semgrep OSS repository mapping file is invalid",
    ):
        get_semgrep_oss_repository_mappings(LocalReportReader(str(fixture_path)))


def test_get_semgrep_oss_report_rejects_multiple_artifacts():
    fixture_path = Path("tests/data/semgrep/multiple_report_artifacts")
    assert get_semgrep_oss_report(LocalReportReader(str(fixture_path))) is None


def test_get_semgrep_oss_report_rejects_non_semgrep_json():
    fixture_path = Path("tests/data/semgrep/non_semgrep_report.json")
    assert get_semgrep_oss_report(LocalReportReader(str(fixture_path))) is None


def test_get_semgrep_oss_report_rejects_zero_artifacts(tmp_path):
    assert get_semgrep_oss_report(LocalReportReader(str(tmp_path))) is None


def test_build_oss_sast_finding_id_prefers_fingerprint_when_present():
    first_id = _build_oss_sast_finding_id(
        "python.lang.security.audit.sql-injection.fake-1",
        "/workspace/chatbox-sandbox/app/auth.py",
        "42",
        "9",
        "42",
        "61",
        "https://github.com/subimagesec/subimage",
        "fake-fingerprint-1",
    )
    second_id = _build_oss_sast_finding_id(
        "python.lang.security.audit.sql-injection.fake-1",
        "/workspace/chatbox-sandbox/app/auth.py",
        "420",
        "90",
        "420",
        "610",
        "https://github.com/subimagesec/subimage",
        "fake-fingerprint-1",
    )

    assert first_id.startswith("semgrep-oss-sast-")
    assert second_id.startswith("semgrep-oss-sast-")
    assert first_id == second_id


def test_build_oss_sast_finding_id_uses_repository_url_with_fingerprint():
    repo_a_id = _build_oss_sast_finding_id(
        "python.lang.security.audit.sql-injection.fake-1",
        "/workspace/chatbox-sandbox/app/auth.py",
        "42",
        "9",
        "42",
        "61",
        "https://github.com/subimagesec/subimage",
        "fake-fingerprint-1",
    )
    repo_b_id = _build_oss_sast_finding_id(
        "python.lang.security.audit.sql-injection.fake-1",
        "/workspace/chatbox-sandbox/app/auth.py",
        "42",
        "9",
        "42",
        "61",
        "https://github.com/different-org/different-repo",
        "fake-fingerprint-1",
    )

    assert repo_a_id.startswith("semgrep-oss-sast-")
    assert repo_b_id.startswith("semgrep-oss-sast-")
    assert repo_a_id != repo_b_id
