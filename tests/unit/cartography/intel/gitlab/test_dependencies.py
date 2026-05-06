import gzip
import io
import json
import zipfile
from unittest.mock import Mock

import pytest

from cartography.intel.gitlab.dependencies import _parse_cyclonedx_sbom
from cartography.intel.gitlab.dependencies import _select_dependency_scan_job
from cartography.intel.gitlab.dependencies import (
    AUTODEVOPS_MAVEN_DEPENDENCY_SCAN_JOB_NAME,
)
from cartography.intel.gitlab.dependencies import (
    AUTODEVOPS_PYTHON_DEPENDENCY_SCAN_JOB_NAME,
)
from cartography.intel.gitlab.dependencies import DEFAULT_DEPENDENCY_SCAN_JOB_NAME
from cartography.intel.gitlab.dependencies import get_dependencies


def _build_artifacts_zip(files: dict[str, dict | bytes]) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        for path, payload in files.items():
            if isinstance(payload, bytes):
                archive.writestr(path, payload)
            else:
                archive.writestr(path, json.dumps(payload))
    return buffer.getvalue()


def _build_gzip_json(payload: dict) -> bytes:
    return gzip.compress(json.dumps(payload).encode("utf-8"))


def _build_response(
    *,
    status_code: int = 200,
    json_data: list[dict] | None = None,
    content: bytes = b"",
    headers: dict[str, str] | None = None,
) -> Mock:
    response = Mock()
    response.status_code = status_code
    response.headers = headers or {}
    response.content = content
    response.raise_for_status.return_value = None
    if json_data is not None:
        response.json.return_value = json_data
    return response


def test_parse_cyclonedx_sbom_links_manifest_from_metadata():
    """
    Test that manifest_id is correctly looked up from SBOM metadata property
    'gitlab:dependency_scanning:input_file'.

    GitLab stores the source manifest file in the SBOM metadata, and ALL
    dependencies in that SBOM came from that single manifest file.
    """
    # Arrange: SBOM with metadata specifying the input file
    sbom_data = {
        "metadata": {
            "properties": [
                {
                    "name": "gitlab:dependency_scanning:input_file:path",
                    "value": "package.json",
                },
            ],
        },
        "components": [
            {
                "type": "library",
                "name": "express",
                "version": "4.18.2",
                "purl": "pkg:npm/express@4.18.2",
            },
            {
                "type": "library",
                "name": "lodash",
                "version": "4.17.21",
                "purl": "pkg:npm/lodash@4.17.21",
            },
        ],
    }

    # Arrange: dependency_files with matching path
    dependency_files = [
        {
            "id": "https://gitlab.com/org/project/blob/package.json",
            "path": "package.json",
        },
    ]

    # Act
    result = _parse_cyclonedx_sbom(sbom_data, dependency_files)

    # Assert: ALL dependencies should have manifest_id set from metadata
    assert len(result) == 2

    # First dependency
    dep1 = result[0]
    assert dep1["name"] == "express"
    assert dep1["version"] == "4.18.2"
    assert dep1["manifest_path"] == "package.json"
    assert dep1["manifest_id"] == "https://gitlab.com/org/project/blob/package.json"

    # Second dependency
    dep2 = result[1]
    assert dep2["name"] == "lodash"
    assert dep2["version"] == "4.17.21"
    assert dep2["manifest_path"] == "package.json"
    assert dep2["manifest_id"] == "https://gitlab.com/org/project/blob/package.json"


def test_parse_cyclonedx_sbom_no_manifest_id_when_path_not_found():
    """
    Test that when manifest path from metadata doesn't match any dependency file,
    manifest_id is not set (but manifest_path is still preserved).
    """
    # Arrange: SBOM with path that doesn't exist in dependency_files
    sbom_data = {
        "metadata": {
            "properties": [
                {
                    "name": "gitlab:dependency_scanning:input_file:path",
                    "value": "packages/client/package.json",
                },
            ],
        },
        "components": [
            {
                "type": "library",
                "name": "axios",
                "version": "1.6.0",
                "purl": "pkg:npm/axios@1.6.0",
            },
        ],
    }

    # Arrange: dependency_files without matching path
    dependency_files = [
        {
            "id": "https://gitlab.com/org/project/blob/package.json",
            "path": "package.json",
        },
    ]

    # Act
    result = _parse_cyclonedx_sbom(sbom_data, dependency_files)

    # Assert: manifest_path is set but manifest_id is not
    assert len(result) == 1
    dep = result[0]
    assert dep["name"] == "axios"
    assert dep["manifest_path"] == "packages/client/package.json"
    assert "manifest_id" not in dep


def test_parse_cyclonedx_sbom_no_metadata_properties():
    """
    Test that when SBOM has no metadata properties, dependencies are still
    parsed but without manifest linking.
    """
    # Arrange: SBOM without metadata properties
    sbom_data = {
        "components": [
            {
                "type": "library",
                "name": "react",
                "version": "18.2.0",
                "purl": "pkg:npm/react@18.2.0",
            },
        ],
    }

    # Arrange: dependency_files available but won't match
    dependency_files = [
        {
            "id": "https://gitlab.com/org/project/blob/package.json",
            "path": "package.json",
        },
    ]

    # Act
    result = _parse_cyclonedx_sbom(sbom_data, dependency_files)

    # Assert: dependency is parsed but no manifest linking
    assert len(result) == 1
    dep = result[0]
    assert dep["name"] == "react"
    assert dep["manifest_path"] == ""
    assert "manifest_id" not in dep


def test_parse_cyclonedx_sbom_skips_non_library_components():
    """
    Test that non-library components (like applications) are skipped.
    """
    # Arrange: SBOM with application component
    sbom_data = {
        "metadata": {
            "properties": [
                {
                    "name": "gitlab:dependency_scanning:input_file:path",
                    "value": "package.json",
                },
            ],
        },
        "components": [
            {
                "type": "application",
                "name": "my-app",
                "version": "1.0.0",
            },
            {
                "type": "library",
                "name": "react",
                "version": "18.2.0",
                "purl": "pkg:npm/react@18.2.0",
            },
        ],
    }

    # Act
    result = _parse_cyclonedx_sbom(sbom_data, [])

    # Assert: only library component is returned
    assert len(result) == 1
    assert result[0]["name"] == "react"


def test_parse_cyclonedx_sbom_extracts_package_manager_from_purl():
    """
    Test that package manager is correctly extracted from purl.
    """
    # Arrange: SBOM with various package types
    sbom_data = {
        "components": [
            {
                "type": "library",
                "name": "express",
                "version": "4.18.2",
                "purl": "pkg:npm/express@4.18.2",
            },
            {
                "type": "library",
                "name": "requests",
                "version": "2.31.0",
                "purl": "pkg:pypi/requests@2.31.0",
            },
            {
                "type": "library",
                "name": "no-purl-lib",
                "version": "1.0.0",
                # No purl
            },
        ],
    }

    # Act
    result = _parse_cyclonedx_sbom(sbom_data, [])

    # Assert: package managers correctly extracted
    assert len(result) == 3
    assert result[0]["package_manager"] == "npm"
    assert result[1]["package_manager"] == "pypi"
    assert result[2]["package_manager"] == "unknown"


def test_parse_cyclonedx_sbom_skips_components_without_name():
    """
    Test that components without a name are skipped.
    """
    # Arrange: SBOM with nameless component
    sbom_data = {
        "components": [
            {
                "type": "library",
                "version": "1.0.0",
                # No name
            },
            {
                "type": "library",
                "name": "valid-lib",
                "version": "1.0.0",
            },
        ],
    }

    # Act
    result = _parse_cyclonedx_sbom(sbom_data, [])

    # Assert: only named component is returned
    assert len(result) == 1
    assert result[0]["name"] == "valid-lib"


def test_select_dependency_scan_job_supports_autodevops_job_names():
    jobs = [
        {
            "id": 300,
            "name": AUTODEVOPS_PYTHON_DEPENDENCY_SCAN_JOB_NAME,
            "ref": "feature-branch",
        },
        {
            "id": 299,
            "name": DEFAULT_DEPENDENCY_SCAN_JOB_NAME,
            "ref": "main",
        },
    ]

    job = _select_dependency_scan_job(jobs, None)

    assert job is not None
    assert job["id"] == 300
    assert job["name"] == AUTODEVOPS_PYTHON_DEPENDENCY_SCAN_JOB_NAME


def test_select_dependency_scan_job_prefers_default_branch():
    jobs = [
        {
            "id": 300,
            "name": AUTODEVOPS_PYTHON_DEPENDENCY_SCAN_JOB_NAME,
            "ref": "feature-branch",
        },
        {
            "id": 299,
            "name": DEFAULT_DEPENDENCY_SCAN_JOB_NAME,
            "ref": "main",
        },
    ]

    job = _select_dependency_scan_job(jobs, None, "main")

    assert job is not None
    assert job["id"] == 299
    assert job["name"] == DEFAULT_DEPENDENCY_SCAN_JOB_NAME


def test_select_dependency_scan_job_honors_custom_name_only():
    jobs = [
        {"id": 200, "name": AUTODEVOPS_MAVEN_DEPENDENCY_SCAN_JOB_NAME},
        {"id": 199, "name": DEFAULT_DEPENDENCY_SCAN_JOB_NAME},
    ]

    job = _select_dependency_scan_job(jobs, "custom-dependency-job")

    assert job is None


def test_get_dependencies_uses_selected_job_id_for_artifacts(
    mocker,
) -> None:
    jobs_response = _build_response(
        json_data=[
            {
                "id": 300,
                "name": AUTODEVOPS_PYTHON_DEPENDENCY_SCAN_JOB_NAME,
                "ref": "main",
            },
            {
                "id": 299,
                "name": DEFAULT_DEPENDENCY_SCAN_JOB_NAME,
                "ref": "main",
            },
        ]
    )
    artifacts_response = _build_response(
        content=_build_artifacts_zip(
            {
                "gl-sbom-npm.cdx.json": {
                    "metadata": {
                        "properties": [
                            {
                                "name": "gitlab:dependency_scanning:input_file:path",
                                "value": "package.json",
                            },
                        ],
                    },
                    "components": [
                        {
                            "type": "library",
                            "name": "express",
                            "version": "4.18.2",
                            "purl": "pkg:npm/express@4.18.2",
                        },
                    ],
                },
            }
        )
    )
    request = mocker.patch(
        "cartography.intel.gitlab.dependencies.make_request_with_retry",
        side_effect=[jobs_response, artifacts_response],
    )
    mocker.patch("cartography.intel.gitlab.dependencies.check_rate_limit_remaining")

    dependencies = get_dependencies(
        "https://gitlab.example.com",
        "token",
        42,
        [
            {
                "id": "https://gitlab.example.com/group/project/-/blob/main/package.json",
                "path": "package.json",
            },
        ],
    )

    assert dependencies == [
        {
            "name": "express",
            "version": "4.18.2",
            "package_manager": "npm",
            "manifest_path": "package.json",
            "manifest_id": "https://gitlab.example.com/group/project/-/blob/main/package.json",
        },
    ]
    assert (
        request.call_args_list[1].args[1]
        == "https://gitlab.example.com/api/v4/projects/42/jobs/300/artifacts"
    )
    assert len(request.call_args_list[1].args) == 3


def test_get_dependencies_paginates_jobs_and_prefers_default_branch(mocker) -> None:
    first_page_jobs = [
        {
            "id": index,
            "name": "test",
            "ref": "main",
        }
        for index in range(1000, 1100)
    ]
    first_page = _build_response(
        json_data=first_page_jobs,
        headers={"X-Next-Page": "2"},
    )
    second_page = _build_response(
        json_data=[
            {
                "id": 501,
                "name": AUTODEVOPS_PYTHON_DEPENDENCY_SCAN_JOB_NAME,
                "ref": "feature-branch",
                "artifacts": [],
            },
            {
                "id": 500,
                "name": DEFAULT_DEPENDENCY_SCAN_JOB_NAME,
                "ref": "main",
                "artifacts": [],
            },
        ],
    )
    artifacts_response = _build_response(
        content=_build_artifacts_zip(
            {
                "gl-sbom-pypi-pip.cdx.json": {
                    "metadata": {
                        "properties": [
                            {
                                "name": "gitlab:dependency_scanning:input_file:path",
                                "value": "requirements.txt",
                            },
                        ],
                    },
                    "components": [
                        {
                            "type": "library",
                            "name": "requests",
                            "version": "2.31.0",
                            "purl": "pkg:pypi/requests@2.31.0",
                        },
                    ],
                },
            }
        )
    )
    request = mocker.patch(
        "cartography.intel.gitlab.dependencies.make_request_with_retry",
        side_effect=[first_page, second_page, artifacts_response],
    )
    mocker.patch("cartography.intel.gitlab.dependencies.check_rate_limit_remaining")

    dependencies = get_dependencies(
        "https://gitlab.example.com",
        "token",
        42,
        [
            {
                "id": "https://gitlab.example.com/group/project/-/blob/main/requirements.txt",
                "path": "requirements.txt",
            },
        ],
        default_branch="main",
    )

    assert dependencies == [
        {
            "name": "requests",
            "version": "2.31.0",
            "package_manager": "pypi",
            "manifest_path": "requirements.txt",
            "manifest_id": "https://gitlab.example.com/group/project/-/blob/main/requirements.txt",
        },
    ]
    assert request.call_args_list[0].args[3]["page"] == 1
    assert request.call_args_list[1].args[3]["page"] == 2
    assert (
        request.call_args_list[2].args[1]
        == "https://gitlab.example.com/api/v4/projects/42/jobs/500/artifacts"
    )


def test_get_dependencies_parses_gzipped_cyclonedx_from_archive(mocker) -> None:
    jobs_response = _build_response(
        json_data=[
            {
                "id": 700,
                "name": AUTODEVOPS_PYTHON_DEPENDENCY_SCAN_JOB_NAME,
                "ref": "main",
                "artifacts": [
                    {
                        "file_type": "cyclonedx",
                        "filename": "gl-sbom.cdx.json.gz",
                        "size": 2151,
                    },
                ],
            },
        ]
    )
    artifacts_response = _build_response(
        content=_build_artifacts_zip(
            {
                "gl-sbom.cdx.json.gz": _build_gzip_json(
                    {
                        "metadata": {
                            "properties": [
                                {
                                    "name": "gitlab:dependency_scanning:input_file:path",
                                    "value": "requirements.txt",
                                },
                            ],
                        },
                        "components": [
                            {
                                "type": "library",
                                "name": "urllib3",
                                "version": "2.2.1",
                                "purl": "pkg:pypi/urllib3@2.2.1",
                            },
                        ],
                    }
                ),
            }
        )
    )
    mocker.patch(
        "cartography.intel.gitlab.dependencies.make_request_with_retry",
        side_effect=[jobs_response, artifacts_response],
    )
    mocker.patch("cartography.intel.gitlab.dependencies.check_rate_limit_remaining")

    dependencies = get_dependencies(
        "https://gitlab.example.com",
        "token",
        42,
        [
            {
                "id": "https://gitlab.example.com/group/project/-/blob/main/requirements.txt",
                "path": "requirements.txt",
            },
        ],
        default_branch="main",
    )

    assert dependencies == [
        {
            "name": "urllib3",
            "version": "2.2.1",
            "package_manager": "pypi",
            "manifest_path": "requirements.txt",
            "manifest_id": "https://gitlab.example.com/group/project/-/blob/main/requirements.txt",
        },
    ]


def test_get_dependencies_parses_direct_gzipped_cyclonedx_response(mocker) -> None:
    jobs_response = _build_response(
        json_data=[
            {
                "id": 701,
                "name": AUTODEVOPS_PYTHON_DEPENDENCY_SCAN_JOB_NAME,
                "ref": "main",
                "artifacts": [
                    {
                        "file_type": "cyclonedx",
                        "filename": "gl-sbom.cdx.json.gz",
                        "size": 2151,
                    },
                ],
            },
        ]
    )
    artifacts_response = _build_response(
        content=_build_gzip_json(
            {
                "metadata": {
                    "properties": [
                        {
                            "name": "gitlab:dependency_scanning:input_file:path",
                            "value": "requirements.txt",
                        },
                    ],
                },
                "components": [
                    {
                        "type": "library",
                        "name": "urllib3",
                        "version": "2.2.1",
                        "purl": "pkg:pypi/urllib3@2.2.1",
                    },
                ],
            }
        )
    )
    mocker.patch(
        "cartography.intel.gitlab.dependencies.make_request_with_retry",
        side_effect=[jobs_response, artifacts_response],
    )
    mocker.patch("cartography.intel.gitlab.dependencies.check_rate_limit_remaining")

    dependencies = get_dependencies(
        "https://gitlab.example.com",
        "token",
        42,
        [
            {
                "id": "https://gitlab.example.com/group/project/-/blob/main/requirements.txt",
                "path": "requirements.txt",
            },
        ],
        default_branch="main",
    )

    assert dependencies == [
        {
            "name": "urllib3",
            "version": "2.2.1",
            "package_manager": "pypi",
            "manifest_path": "requirements.txt",
            "manifest_id": "https://gitlab.example.com/group/project/-/blob/main/requirements.txt",
        },
    ]


def test_get_dependencies_downloads_raw_cyclonedx_artifact_when_archive_has_no_sbom(
    mocker,
) -> None:
    jobs_response = _build_response(
        json_data=[
            {
                "id": 702,
                "name": AUTODEVOPS_PYTHON_DEPENDENCY_SCAN_JOB_NAME,
                "ref": "main",
                "artifacts": [
                    {
                        "file_type": "archive",
                        "filename": "artifacts.zip",
                        "size": 2250,
                    },
                    {
                        "file_type": "cyclonedx",
                        "filename": "gl-sbom.cdx.json.gz",
                        "size": 2151,
                    },
                ],
            },
        ]
    )
    archive_response = _build_response(content=_build_artifacts_zip({}))
    raw_artifact_response = _build_response(
        content=_build_gzip_json(
            {
                "components": [
                    {
                        "type": "library",
                        "name": "urllib3",
                        "version": "2.2.1",
                        "purl": "pkg:pypi/urllib3@2.2.1",
                    },
                ],
            }
        )
    )
    request = mocker.patch(
        "cartography.intel.gitlab.dependencies.make_request_with_retry",
        side_effect=[jobs_response, archive_response, raw_artifact_response],
    )
    mocker.patch("cartography.intel.gitlab.dependencies.check_rate_limit_remaining")

    dependencies = get_dependencies(
        "https://gitlab.example.com",
        "token",
        42,
        [],
        default_branch="main",
    )

    assert dependencies == [
        {
            "name": "urllib3",
            "version": "2.2.1",
            "package_manager": "pypi",
            "manifest_path": "",
        },
    ]
    assert (
        request.call_args_list[2].args[1]
        == "https://gitlab.example.com/api/v4/projects/42/jobs/702/artifacts/gl-sbom.cdx.json.gz"
    )


def test_get_dependencies_returns_empty_and_logs_warning_on_forbidden_artifacts(
    mocker,
    caplog,
) -> None:
    jobs_response = _build_response(
        json_data=[
            {
                "id": 703,
                "name": AUTODEVOPS_PYTHON_DEPENDENCY_SCAN_JOB_NAME,
                "ref": "main",
                "artifacts": [],
            },
        ]
    )
    artifacts_response = _build_response(status_code=403)
    mocker.patch(
        "cartography.intel.gitlab.dependencies.make_request_with_retry",
        side_effect=[jobs_response, artifacts_response],
    )
    mocker.patch("cartography.intel.gitlab.dependencies.check_rate_limit_remaining")

    dependencies = get_dependencies(
        "https://gitlab.example.com",
        "token",
        42,
        [],
        default_branch="main",
    )

    assert dependencies == []
    assert "download CI job artifacts" in caplog.text
    assert "Developer or Maintainer access" in caplog.text


def test_get_dependencies_propagates_invalid_gzip_cyclonedx(mocker) -> None:
    jobs_response = _build_response(
        json_data=[
            {
                "id": 704,
                "name": AUTODEVOPS_PYTHON_DEPENDENCY_SCAN_JOB_NAME,
                "ref": "main",
                "artifacts": [
                    {
                        "file_type": "cyclonedx",
                        "filename": "gl-sbom.cdx.json.gz",
                    },
                ],
            },
        ]
    )
    artifacts_response = _build_response(
        content=_build_artifacts_zip({"gl-sbom.cdx.json.gz": b"not gzip"})
    )
    mocker.patch(
        "cartography.intel.gitlab.dependencies.make_request_with_retry",
        side_effect=[jobs_response, artifacts_response],
    )
    mocker.patch("cartography.intel.gitlab.dependencies.check_rate_limit_remaining")

    with pytest.raises(gzip.BadGzipFile):
        get_dependencies(
            "https://gitlab.example.com",
            "token",
            42,
            [],
            default_branch="main",
        )
