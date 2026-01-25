from cartography.intel.gitlab.dependencies import _parse_cyclonedx_sbom


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
