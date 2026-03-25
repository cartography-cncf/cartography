from cartography.intel.gitlab.dependencies import _parse_cyclonedx_sbom
from cartography.intel.gitlab.dependencies import transform_dependencies


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
    assert dep1["purl"] == "pkg:npm/express@4.18.2"

    # Second dependency
    dep2 = result[1]
    assert dep2["name"] == "lodash"
    assert dep2["version"] == "4.17.21"
    assert dep2["manifest_path"] == "package.json"
    assert dep2["manifest_id"] == "https://gitlab.com/org/project/blob/package.json"
    assert dep2["purl"] == "pkg:npm/lodash@4.17.21"


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
    assert dep["purl"] == "pkg:npm/axios@1.6.0"


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
    assert dep["purl"] == "pkg:npm/react@18.2.0"


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


def test_parse_cyclonedx_sbom_preserves_purl():
    """
    Test that purl is passed through from CycloneDX components.
    """
    sbom_data = {
        "components": [
            {
                "type": "library",
                "name": "Django",
                "version": "4.2.0",
                "purl": "pkg:pypi/Django@4.2.0",
            },
            {
                "type": "library",
                "name": "no-purl",
                "version": "1.0.0",
            },
        ],
    }

    result = _parse_cyclonedx_sbom(sbom_data, [])

    assert result[0]["purl"] == "pkg:pypi/Django@4.2.0"
    assert result[1]["purl"] is None


def test_transform_dependencies_computes_derived_fields():
    """
    Test that transform_dependencies computes ecosystem, purl-derived fields,
    canonical names, and requirements from manifest parsing.
    """
    raw_deps = [
        {
            "name": "Django",
            "version": "4.2.0",
            "package_manager": "pypi",
            "manifest_path": "requirements.txt",
            "purl": "pkg:pypi/Django@4.2.0",
        },
    ]
    requirements = {
        "requirements.txt": {
            "django": ">=4.2,<5.0",
        },
    }

    result = transform_dependencies(
        raw_deps,
        "https://gitlab.com/org/project",
        requirements,
    )

    assert len(result) == 1
    dep = result[0]
    assert dep["name"] == "django"  # Canonicalized
    assert dep["original_name"] == "Django"
    assert dep["ecosystem"] == "pypi"
    assert dep["type"] == "pypi"
    assert dep["purl"] == "pkg:pypi/Django@4.2.0"
    assert dep["normalized_id"] == "pypi|django|4.2.0"
    assert dep["requirements"] == ">=4.2,<5.0"
    assert dep["manifest_file"] == "requirements.txt"


def test_transform_dependencies_no_requirements():
    """
    Test that transform works when no requirements are available.
    """
    raw_deps = [
        {
            "name": "express",
            "version": "4.18.2",
            "package_manager": "npm",
            "manifest_path": "package.json",
            "purl": "pkg:npm/express@4.18.2",
        },
    ]

    result = transform_dependencies(raw_deps, "https://gitlab.com/org/project")

    assert len(result) == 1
    dep = result[0]
    assert dep["requirements"] is None
    assert dep["ecosystem"] == "npm"
    assert dep["type"] == "npm"
    assert dep["normalized_id"] == "npm|express|4.18.2"


def test_transform_dependencies_no_purl():
    """
    Test that transform handles dependencies without purl gracefully.
    """
    raw_deps = [
        {
            "name": "some-lib",
            "version": "1.0.0",
            "package_manager": "unknown",
            "manifest_path": "",
            "purl": None,
        },
    ]

    result = transform_dependencies(raw_deps, "https://gitlab.com/org/project")

    assert len(result) == 1
    dep = result[0]
    assert dep["type"] is None
    assert dep["normalized_id"] is None
    assert dep["purl"] is None
