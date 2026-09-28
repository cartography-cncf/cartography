from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.miradore.config_profiles
import cartography.intel.miradore.devices
import cartography.intel.miradore.locations
import cartography.intel.miradore.organizations
import cartography.intel.miradore.tags
import cartography.intel.miradore.users
from tests.data.miradore.config_profiles import CONFIG_PROFILES
from tests.data.miradore.devices import DEVICES
from tests.data.miradore.locations import LOCATIONS
from tests.data.miradore.organizations import ORGANIZATIONS
from tests.data.miradore.tags import TAGS
from tests.data.miradore.users import USERS
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_SITE_NAME = "simpsoncorp"
OTHER_SITE_NAME = "southpark"
TEST_BASE_URI = "https://online.miradore.com"
TEST_API_KEY = "1_AaDf234sdf8!4"


def _sync_everything(
    neo4j_session,
    site_name: str = TEST_SITE_NAME,
    update_tag: int = TEST_UPDATE_TAG,
) -> None:
    args = (
        neo4j_session,
        MagicMock(),
        TEST_BASE_URI,
        site_name,
        TEST_API_KEY,
        update_tag,
        {"UPDATE_TAG": update_tag, "TENANT_ID": site_name},
    )
    cartography.intel.miradore.organizations.sync(*args)
    cartography.intel.miradore.locations.sync(*args)
    cartography.intel.miradore.tags.sync(*args)
    cartography.intel.miradore.config_profiles.sync(*args)
    cartography.intel.miradore.users.sync(*args)
    cartography.intel.miradore.devices.sync(*args)


@patch.object(
    cartography.intel.miradore.organizations, "get", return_value=ORGANIZATIONS
)
@patch.object(cartography.intel.miradore.locations, "get", return_value=LOCATIONS)
@patch.object(cartography.intel.miradore.tags, "get", return_value=TAGS)
@patch.object(
    cartography.intel.miradore.config_profiles, "get", return_value=CONFIG_PROFILES
)
@patch.object(cartography.intel.miradore.users, "get", return_value=USERS)
@patch.object(cartography.intel.miradore.devices, "get", return_value=DEVICES)
def test_sync_miradore(
    mock_devices_get,
    mock_users_get,
    mock_config_profiles_get,
    mock_tags_get,
    mock_locations_get,
    mock_organizations_get,
    neo4j_session,
):
    # Arrange
    neo4j_session.run("MATCH (n) DETACH DELETE n")

    # Act
    _sync_everything(neo4j_session)

    # Assert: the tenant is created from the site name
    assert check_nodes(neo4j_session, "MiradoreTenant", ["id"]) == {(TEST_SITE_NAME,)}

    # Assert: the graph identity is tenant-scoped while the raw Miradore ID is kept
    assert check_nodes(
        neo4j_session,
        "MiradoreDevice",
        ["id", "miradore_id", "hostname", "serial_number", "platform", "os_version"],
    ) == {
        (
            "simpsoncorp/1001",
            1001,
            "marge-macbook",
            "C02XY1234567",
            "macOS",
            "15.5",
        ),
        ("simpsoncorp/1002", 1002, "bart-iphone", "F2LX9ABCDEFG", "iOS", "18.5"),
        ("simpsoncorp/1003", 1003, "lisa-pixel", "PIXEL8SERIAL01", "Android", "15"),
        (
            "simpsoncorp/1004",
            1004,
            "homer-workstation",
            "DELL7X8Y9Z0",
            "WindowsDesktop",
            "10.0.22631",
        ),
    }

    # Assert: every node type is attached to the tenant
    for label, expected_ids in (
        ("MiradoreDevice", {1001, 1002, 1003, 1004}),
        ("MiradoreUser", {2001, 2002}),
        ("MiradoreOrganization", {3001, 3002}),
        ("MiradoreLocation", {4001, 4002}),
        ("MiradoreConfigProfile", {8001, 8002}),
        ("MiradoreConfigProfileDeployment", {7001, 7002, 7003}),
    ):
        assert check_rels(
            neo4j_session,
            "MiradoreTenant",
            "id",
            label,
            "id",
            "RESOURCE",
            rel_direction_right=True,
        ) == {
            (TEST_SITE_NAME, f"{TEST_SITE_NAME}/{node_id}") for node_id in expected_ids
        }
    assert check_rels(
        neo4j_session,
        "MiradoreTenant",
        "id",
        "MiradoreTag",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        (TEST_SITE_NAME, "simpsoncorp/engineering"),
        (TEST_SITE_NAME, "simpsoncorp/byod"),
        (TEST_SITE_NAME, "simpsoncorp/unused"),
    }

    # Assert: users own their devices
    assert check_rels(
        neo4j_session,
        "MiradoreUser",
        "miradore_id",
        "MiradoreDevice",
        "miradore_id",
        "OWNS",
        rel_direction_right=True,
    ) == {
        (2001, 1001),
        (2001, 1002),
        (2002, 1004),
    }

    # Assert: devices belong to their organization
    assert check_rels(
        neo4j_session,
        "MiradoreDevice",
        "miradore_id",
        "MiradoreOrganization",
        "miradore_id",
        "MEMBER_OF",
        rel_direction_right=True,
    ) == {
        (1001, 3001),
        (1002, 3002),
        (1003, 3002),
        (1004, 3001),
    }

    # Assert: devices belong to their location
    assert check_rels(
        neo4j_session,
        "MiradoreDevice",
        "miradore_id",
        "MiradoreLocation",
        "miradore_id",
        "MEMBER_OF",
        rel_direction_right=True,
    ) == {
        (1001, 4001),
        (1002, 4001),
        (1003, 4002),
        (1004, 4002),
    }

    # Assert: the organization and location hierarchies are wired
    assert check_rels(
        neo4j_session,
        "MiradoreOrganization",
        "miradore_id",
        "MiradoreOrganization",
        "miradore_id",
        "MEMBER_OF",
        rel_direction_right=True,
    ) == {(3002, 3001)}
    assert check_rels(
        neo4j_session,
        "MiradoreLocation",
        "miradore_id",
        "MiradoreLocation",
        "miradore_id",
        "MEMBER_OF",
        rel_direction_right=True,
    ) == {(4002, 4001)}

    # Assert: device tags, including the single-tag case xmltodict collapses to a dict
    assert check_rels(
        neo4j_session,
        "MiradoreDevice",
        "miradore_id",
        "MiradoreTag",
        "name",
        "TAGGED",
        rel_direction_right=True,
    ) == {
        (1001, "engineering"),
        (1002, "engineering"),
        (1002, "byod"),
    }

    # Assert: deployments link the device to the profile it installs
    assert check_rels(
        neo4j_session,
        "MiradoreDevice",
        "miradore_id",
        "MiradoreConfigProfileDeployment",
        "miradore_id",
        "HAS_DEPLOYMENT",
        rel_direction_right=True,
    ) == {
        (1001, 7001),
        (1001, 7002),
        (1002, 7003),
    }
    assert check_rels(
        neo4j_session,
        "MiradoreConfigProfileDeployment",
        "miradore_id",
        "MiradoreConfigProfile",
        "miradore_id",
        "DEPLOYS",
        rel_direction_right=True,
    ) == {
        (7001, 8001),
        (7002, 8002),
        (7003, 8002),
    }

    # Cleanup
    neo4j_session.run("MATCH (n) DETACH DELETE n")


@patch.object(
    cartography.intel.miradore.organizations, "get", return_value=ORGANIZATIONS
)
@patch.object(cartography.intel.miradore.locations, "get", return_value=LOCATIONS)
@patch.object(cartography.intel.miradore.tags, "get", return_value=TAGS)
@patch.object(
    cartography.intel.miradore.config_profiles, "get", return_value=CONFIG_PROFILES
)
@patch.object(cartography.intel.miradore.users, "get", return_value=USERS)
@patch.object(cartography.intel.miradore.devices, "get", return_value=DEVICES)
def test_two_tenants_with_the_same_miradore_ids_stay_isolated(
    mock_devices_get,
    mock_users_get,
    mock_config_profiles_get,
    mock_tags_get,
    mock_locations_get,
    mock_organizations_get,
    neo4j_session,
):
    """Miradore numbers items per tenant, so two sites share raw IDs like Device 1001.

    The graph merges nodes on `id` alone, so an unscoped identity would make the second
    sync overwrite the first tenant's properties and cross-wire its relationships.
    """
    # Arrange
    neo4j_session.run("MATCH (n) DETACH DELETE n")

    # Act: sync the very same fixtures under two different site names
    _sync_everything(neo4j_session, TEST_SITE_NAME)
    _sync_everything(neo4j_session, OTHER_SITE_NAME, TEST_UPDATE_TAG + 1)

    # Assert: both tenants keep their own device nodes rather than merging into one
    assert check_nodes(neo4j_session, "MiradoreDevice", ["id", "miradore_id"]) == {
        ("simpsoncorp/1001", 1001),
        ("simpsoncorp/1002", 1002),
        ("simpsoncorp/1003", 1003),
        ("simpsoncorp/1004", 1004),
        ("southpark/1001", 1001),
        ("southpark/1002", 1002),
        ("southpark/1003", 1003),
        ("southpark/1004", 1004),
    }

    # Assert: no device is attached to more than one tenant
    assert (
        neo4j_session.run(
            """
            MATCH (t:MiradoreTenant)-[:RESOURCE]->(d:MiradoreDevice)
            WITH d, count(DISTINCT t) AS tenants WHERE tenants > 1
            RETURN count(d) AS count
            """
        ).single()["count"]
        == 0
    )

    # Assert: no relationship crosses a tenant boundary. Every edge between two Miradore
    # nodes must stay within the site that owns both endpoints.
    assert (
        neo4j_session.run(
            """
            MATCH (a)-[r]->(b)
            WHERE any(l IN labels(a) WHERE l STARTS WITH 'Miradore')
              AND any(l IN labels(b) WHERE l STARTS WITH 'Miradore')
              AND NOT a:MiradoreTenant AND NOT b:MiradoreTenant
              AND split(a.id, '/')[0] <> split(b.id, '/')[0]
            RETURN count(r) AS count
            """
        ).single()["count"]
        == 0
    )

    # Assert: each tenant's devices only reach that tenant's users
    assert check_rels(
        neo4j_session,
        "MiradoreUser",
        "id",
        "MiradoreDevice",
        "id",
        "OWNS",
        rel_direction_right=True,
    ) == {
        ("simpsoncorp/2001", "simpsoncorp/1001"),
        ("simpsoncorp/2001", "simpsoncorp/1002"),
        ("simpsoncorp/2002", "simpsoncorp/1004"),
        ("southpark/2001", "southpark/1001"),
        ("southpark/2001", "southpark/1002"),
        ("southpark/2002", "southpark/1004"),
    }

    # Cleanup
    neo4j_session.run("MATCH (n) DETACH DELETE n")


@patch.object(
    cartography.intel.miradore.organizations, "get", return_value=ORGANIZATIONS
)
@patch.object(cartography.intel.miradore.locations, "get", return_value=LOCATIONS)
@patch.object(cartography.intel.miradore.tags, "get", return_value=TAGS)
@patch.object(
    cartography.intel.miradore.config_profiles, "get", return_value=CONFIG_PROFILES
)
@patch.object(cartography.intel.miradore.users, "get", return_value=USERS)
@patch.object(cartography.intel.miradore.devices, "get", return_value=DEVICES)
def test_cleanup_is_scoped_to_the_tenant(
    mock_devices_get,
    mock_users_get,
    mock_config_profiles_get,
    mock_tags_get,
    mock_locations_get,
    mock_organizations_get,
    neo4j_session,
):
    # Arrange: an unrelated tenant synced under a different update tag must survive
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    _sync_everything(neo4j_session, OTHER_SITE_NAME, TEST_UPDATE_TAG + 1)

    # Act
    _sync_everything(neo4j_session, TEST_SITE_NAME)

    # Assert: this tenant's cleanup left the other tenant's devices in place
    assert check_rels(
        neo4j_session,
        "MiradoreTenant",
        "id",
        "MiradoreDevice",
        "miradore_id",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        (TEST_SITE_NAME, 1001),
        (TEST_SITE_NAME, 1002),
        (TEST_SITE_NAME, 1003),
        (TEST_SITE_NAME, 1004),
        (OTHER_SITE_NAME, 1001),
        (OTHER_SITE_NAME, 1002),
        (OTHER_SITE_NAME, 1003),
        (OTHER_SITE_NAME, 1004),
    }

    # Cleanup
    neo4j_session.run("MATCH (n) DETACH DELETE n")
