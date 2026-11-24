import pytest

from cartography.intel.crowdstrike.spotlight import transform_applications

CID = "cid-1"


def _item(aid: str, cve_id: str, app: dict) -> dict:
    return {"cid": CID, "aid": aid, "cve": {"id": cve_id}, "apps": [app]}


@pytest.mark.parametrize(
    ("app", "expected"),
    [
        (
            {
                "product_name_version": ".Net Framework 4.8",
                "product_name_normalized": ".Net Framework",
                "vendor_normalized": "Microsoft",
            },
            {
                "name": ".Net Framework",
                "vendor": "Microsoft",
                "version": "4.8",
                "normalized_id": "generic|microsoft/.net framework|4.8",
            },
        ),
        (
            {
                "product_name_version": "universal_forwarder 8.1.1-08187535c166",
                "product_name_normalized": "universal_forwarder",
                "vendor_normalized": "Unknown",
            },
            {
                "name": "universal_forwarder",
                "vendor": "Unknown",
                "version": "8.1.1-08187535c166",
                "normalized_id": "generic|universal_forwarder|8.1.1-08187535c166",
            },
        ),
        (
            {
                "product_name_version": "Windows Server 2022",
                "product_name_normalized": "Windows",
                "vendor_normalized": "Microsoft",
            },
            {
                "name": "Windows",
                "vendor": "Microsoft",
                "version": None,
                "normalized_id": None,
            },
        ),
        (
            {
                "product_name_version": "Edge 120.0",
                "product_name_normalized": "Microsoft Edge",
                "vendor_normalized": "Microsoft",
            },
            {
                "name": "Microsoft Edge",
                "vendor": "Microsoft",
                "version": None,
                "normalized_id": None,
            },
        ),
    ],
)
def test_transform_applications_derives_package_identity(app, expected):
    # Act
    applications = transform_applications([_item("host-1", "CVE-2024-0001", app)])

    # Assert
    assert len(applications) == 1
    assert {key: applications[0][key] for key in expected} == expected


def test_transform_applications_groups_hosts_and_cves_per_application():
    # Arrange
    app = {
        "product_name_version": ".Net Framework 4.8",
        "product_name_normalized": ".Net Framework",
        "vendor_normalized": "Microsoft",
    }
    items = [
        _item("host-1", "CVE-2024-0001", app),
        _item("host-2", "CVE-2024-0001", app),
        _item("host-1", "CVE-2024-0002", app),
    ]

    # Act
    applications = transform_applications(items)

    # Assert
    assert len(applications) == 1
    assert applications[0]["host_ids"] == ["host-1", "host-2"]
    assert applications[0]["cve_ids"] == ["CVE-2024-0001", "CVE-2024-0002"]


def test_transform_applications_keeps_unversioned_products_apart():
    # Arrange
    items = [
        _item(
            "host-1",
            "CVE-2024-0001",
            {
                "product_name_version": "Windows Server 2022",
                "product_name_normalized": "Windows",
                "vendor_normalized": "Microsoft",
            },
        ),
        _item(
            "host-2",
            "CVE-2024-0001",
            {
                "product_name_version": "Windows Server 2019",
                "product_name_normalized": "Windows",
                "vendor_normalized": "Microsoft",
            },
        ),
    ]

    # Act
    applications = transform_applications(items)

    # Assert
    assert sorted(application["host_ids"] for application in applications) == [
        ["host-1"],
        ["host-2"],
    ]
