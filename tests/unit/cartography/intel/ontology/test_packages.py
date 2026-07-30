from cartography.intel.ontology.packages import transform_packages


def test_transform_packages_groups_versions():
    data = [
        {
            "normalized_id": "npm|express|4.18.2",
            "name": "express",
            "version": "4.18.2",
            "type": "npm",
            "purl": "pkg:npm/express@4.18.2",
        },
        {
            "normalized_id": "npm|express|4.17.1",
            "name": "Express",
            "version": "4.17.1",
            "type": "npm",
            "purl": "pkg:npm/express@4.17.1",
        },
    ]

    packages = transform_packages(data)

    assert packages == [
        {
            "id": "npm|express",
            "name": "express",
            "namespace": None,
            "type": "npm",
            "version_ids": ["npm|express|4.17.1", "npm|express|4.18.2"],
        },
    ]


def test_transform_packages_does_not_collide_across_ecosystems():
    data = [
        {
            "normalized_id": "npm|lodash|4.17.21",
            "name": "lodash",
            "version": "4.17.21",
            "type": "npm",
            "purl": "pkg:npm/lodash@4.17.21",
        },
        {
            "normalized_id": "pypi|lodash|1.0.0",
            "name": "lodash",
            "version": "1.0.0",
            "type": "pypi",
            "purl": "pkg:pypi/lodash@1.0.0",
        },
    ]

    packages = {pkg["id"]: pkg for pkg in transform_packages(data)}

    assert set(packages) == {"npm|lodash", "pypi|lodash"}
    assert packages["npm|lodash"]["version_ids"] == ["npm|lodash|4.17.21"]
    assert packages["pypi|lodash"]["version_ids"] == ["pypi|lodash|1.0.0"]


def test_transform_packages_keeps_purl_namespace():
    data = [
        {
            "normalized_id": "npm|@types/node|18.0.0",
            "name": "node",
            "version": "18.0.0",
            "type": "npm",
            "purl": "pkg:npm/%40types/node@18.0.0",
        },
    ]

    (package,) = transform_packages(data)

    assert package["id"] == "npm|@types/node"
    assert package["name"] == "@types/node"
    assert package["namespace"] == "@types"


def test_transform_packages_namespace_is_order_independent():
    """A namespace found on any row of the group wins, whatever the row order is."""
    purl_row = {
        "normalized_id": "npm|@types/node|18.0.0",
        "name": "node",
        "version": "18.0.0",
        "type": "npm",
        "purl": "pkg:npm/%40types/node@18.0.0",
    }
    # Same package reported without a PURL, so its name already carries the scope.
    purl_less_row = {
        "normalized_id": "npm|@types/node|20.0.0",
        "name": "@types/node",
        "version": "20.0.0",
        "type": "npm",
        "purl": None,
    }

    for rows in ([purl_row, purl_less_row], [purl_less_row, purl_row]):
        (package,) = transform_packages(rows)
        assert package["id"] == "npm|@types/node"
        assert package["namespace"] == "@types"
        assert package["version_ids"] == [
            "npm|@types/node|18.0.0",
            "npm|@types/node|20.0.0",
        ]


def test_transform_packages_skips_rows_without_key():
    data = [
        {
            "normalized_id": "npm|express|4.18.2",
            "name": None,
            "version": "4.18.2",
            "type": None,
            "purl": None,
        },
    ]

    assert transform_packages(data) == []
