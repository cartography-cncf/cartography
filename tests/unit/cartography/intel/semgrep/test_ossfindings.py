"""
Unit tests for Semgrep OSS metadata parsing.
"""

from cartography.intel.common.object_store import ListedReportReader
from cartography.intel.common.object_store import ReportRef
from cartography.intel.semgrep.ossfindings import _build_oss_sast_finding_id
from cartography.intel.semgrep.ossfindings import _get_semgrep_oss_repo_context


def test_get_semgrep_oss_repo_context_happy_path():
    metadata_ref = ReportRef(
        uri="s3://semgrep-oss/github/subimagesec/subimage/repo_metadata.yaml",
        name="github/subimagesec/subimage/repo_metadata.yaml",
    )
    metadata_bytes = (
        b'provider: "github"\n'
        b'owner: "subimagesec"\n'
        b'repo: "subimage"\n'
        b'url: "https://github.com/subimagesec/subimage"\n'
        b'branch: "main"\n'
    )
    reader = ListedReportReader(
        source_uri="s3://semgrep-oss/github/subimagesec/subimage/",
        refs=[metadata_ref],
        read_bytes=lambda ref: metadata_bytes,
    )

    assert _get_semgrep_oss_repo_context(reader) == {
        "repositoryName": "subimagesec/subimage",
        "repositoryUrl": "https://github.com/subimagesec/subimage",
        "branch": "main",
    }


def test_build_oss_sast_finding_id_includes_repository_name():
    repo_a_id = _build_oss_sast_finding_id(
        "python.lang.security.audit.sql-injection.fake-1",
        "/workspace/chatbox-sandbox/app/auth.py",
        "42",
        "9",
        "42",
        "61",
        "subimagesec/subimage",
    )
    repo_b_id = _build_oss_sast_finding_id(
        "python.lang.security.audit.sql-injection.fake-1",
        "/workspace/chatbox-sandbox/app/auth.py",
        "42",
        "9",
        "42",
        "61",
        "different-org/different-repo",
    )

    assert repo_a_id.startswith("semgrep-oss-sast-")
    assert repo_b_id.startswith("semgrep-oss-sast-")
    assert repo_a_id != repo_b_id
