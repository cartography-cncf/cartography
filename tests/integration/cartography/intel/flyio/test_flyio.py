from unittest.mock import Mock
from unittest.mock import patch

import cartography.intel.flyio
import cartography.intel.flyio.access_tokens
import cartography.intel.flyio.apps
import cartography.intel.flyio.certificates
import cartography.intel.flyio.ips
import cartography.intel.flyio.machines
import cartography.intel.flyio.releases
import cartography.intel.flyio.secrets
import cartography.intel.flyio.users
import cartography.intel.flyio.volumes
from cartography.client.core.tx import load
from cartography.config import Config
from cartography.models.flyio.app import FlyAppSchema
from tests.data.flyio.access_tokens import APP_ACCESS_TOKENS_RESPONSE
from tests.data.flyio.access_tokens import ORG_ACCESS_TOKENS_RESPONSE
from tests.data.flyio.apps import APPS_RESPONSE
from tests.data.flyio.certificates import CERTIFICATES_RESPONSE
from tests.data.flyio.ips import IPS_RESPONSE
from tests.data.flyio.machines import MACHINES_RESPONSE
from tests.data.flyio.releases import RELEASES_RESPONSE
from tests.data.flyio.secrets import SECRETS_RESPONSE
from tests.data.flyio.users import ORG_MEMBERS_RESPONSE
from tests.data.flyio.volumes import VOLUMES_RESPONSE
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_ORG_SLUG = "jonathanfemi-example-com"
TEST_APP_ID = "jlyv9r258ew18xrg"
TEST_APP_NAME = "nhmhvxo3b9"
TEST_MACHINE_ID = "90802949c92987"
TEST_SERVICE_ID = f"{TEST_MACHINE_ID}/tcp/8000"
TEST_IMAGE_DIGEST = (
    "sha256:b0cbba70b2f1fbb720502cff65ca83bbdbca1e02a78860ce075efdb320eb9802"
)
TEST_IMAGE_ID = f"{TEST_APP_ID}/{TEST_IMAGE_DIGEST}"


@patch.object(
    cartography.intel.flyio.certificates,
    "get",
    return_value=CERTIFICATES_RESPONSE,
)
@patch.object(
    cartography.intel.flyio.secrets,
    "get",
    return_value=SECRETS_RESPONSE,
)
@patch.object(
    cartography.intel.flyio.volumes,
    "get",
    return_value=VOLUMES_RESPONSE,
)
@patch.object(
    cartography.intel.flyio.ips,
    "get",
    return_value=IPS_RESPONSE,
)
@patch.object(
    cartography.intel.flyio.access_tokens,
    "get_app",
    return_value=APP_ACCESS_TOKENS_RESPONSE,
)
@patch.object(
    cartography.intel.flyio.releases,
    "get",
    return_value=RELEASES_RESPONSE,
)
@patch.object(
    cartography.intel.flyio.access_tokens,
    "get_organization",
    return_value=ORG_ACCESS_TOKENS_RESPONSE,
)
@patch.object(
    cartography.intel.flyio.users,
    "get",
    return_value=ORG_MEMBERS_RESPONSE,
)
@patch.object(
    cartography.intel.flyio.machines,
    "get",
    return_value=MACHINES_RESPONSE,
)
@patch.object(
    cartography.intel.flyio.apps,
    "get",
    return_value=APPS_RESPONSE,
)
def test_start_flyio_ingestion(
    mock_apps,
    mock_machines,
    mock_users,
    mock_org_access_tokens,
    mock_releases,
    mock_app_access_tokens,
    mock_ips,
    mock_volumes,
    mock_secrets,
    mock_certificates,
    neo4j_session,
):
    # Arrange
    neo4j_session.run(
        """
        MATCH (n)
        WHERE any(label IN labels(n) WHERE label STARTS WITH 'Fly')
        DETACH DELETE n
        """,
    )
    config = Config(
        neo4j_uri="bolt://localhost:7687",
        flyio_token="test-token",
        flyio_org_slug=TEST_ORG_SLUG,
        flyio_base_url="https://api.machines.dev",
        update_tag=TEST_UPDATE_TAG,
    )

    # Act
    cartography.intel.flyio.start_flyio_ingestion(neo4j_session, config)

    # Assert
    assert check_nodes(
        neo4j_session,
        "FlyOrganization",
        ["id", "name", "slug", "internal_numeric_id"],
    ) == {
        (TEST_ORG_SLUG, "jonathanfemi@example.com", TEST_ORG_SLUG, 977819),
    }
    assert check_nodes(
        neo4j_session,
        "FlyApp",
        ["id", "name", "status", "machine_count", "volume_count"],
    ) == {
        (TEST_APP_ID, TEST_APP_NAME, "deployed", 3, 1),
    }
    assert check_nodes(
        neo4j_session,
        "FlyMachine",
        ["id", "name", "state", "region", "image_repository", "memory_mb"],
    ) == {
        (TEST_MACHINE_ID, "dry-rain-8738", "started", "lhr", TEST_APP_NAME, 1024),
    }
    assert check_nodes(
        neo4j_session,
        "FlyUser",
        ["id", "email"],
    ) == {
        ("Re9RMq7mRleO0UyLAKpq", "jonathanfemi@example.com"),
    }
    assert check_nodes(
        neo4j_session,
        "FlyAccessToken",
        ["id", "name", "revoked"],
    ) == {
        ("app_token_active", "FLY_API_TOKEN", False),
        ("app_token_revoked", "flyctl deploy token", True),
        ("org_token_active", "cartography-flyio-prod-test", False),
    }
    assert check_nodes(
        neo4j_session,
        "FlyRelease",
        ["id", "version", "status", "deployment_strategy", "user_email"],
    ) == {
        (
            "YgoYklRLL8Xo3fBPg6AoX28AG",
            35,
            "succeeded",
            "rolling",
            "jonathanfemi@example.com",
        ),
        ("release_previous", 34, "failed", "immediate", None),
    }
    assert check_nodes(
        neo4j_session,
        "FlyIP",
        ["id", "address", "type", "direction", "is_public"],
    ) == {
        ("ip_v6_id", "2a09:8280:1::66:a54d:0", "v6", "ingress", True),
        ("ip_private_v6_id", "fdaa:10:e286:a7b::1", "private_v6", "ingress", False),
        (
            f"{TEST_APP_ID}/66.241.124.236",
            "66.241.124.236",
            "shared_v4",
            "ingress",
            True,
        ),
        ("egress_v4_id", "66.241.125.42", "egress_v4", "egress", True),
    }
    assert check_nodes(
        neo4j_session,
        "FlyVolume",
        ["id", "name", "encrypted", "attached_machine_id"],
    ) == {
        ("vol_vlykw0x679gyz5p4", "cartography_test_data", True, TEST_MACHINE_ID),
    }
    assert check_nodes(neo4j_session, "FlySecret", ["id", "name"]) == {
        (f"{TEST_APP_ID}/SECRET_KEY", "SECRET_KEY"),
        (f"{TEST_APP_ID}/FLY_API_TOKEN", "FLY_API_TOKEN"),
    }
    certificate = neo4j_session.run(
        """
        MATCH (c:FlyCertificate {id: $id})
        RETURN c.hostname AS hostname,
               c.status AS status,
               c.certificate_authorities AS certificate_authorities,
               c.sources AS sources
        """,
        id=f"{TEST_APP_ID}/www.example.com",
    ).single()
    assert certificate is not None
    assert certificate["hostname"] == "www.example.com"
    assert certificate["status"] == "active"
    assert certificate["certificate_authorities"] == ["lets_encrypt"]
    assert certificate["sources"] == ["fly"]
    assert check_nodes(neo4j_session, "Tenant", ["id", "_ont_name", "_ont_status"]) == {
        (TEST_ORG_SLUG, "jonathanfemi@example.com", None),
        # "deployed" (the raw FlyApp.status, still asserted separately above)
        # normalizes to the shared Tenant canonical status "active".
        (TEST_APP_ID, TEST_APP_NAME, "active"),
    }
    assert check_nodes(
        neo4j_session,
        "UserAccount",
        ["id", "_ont_email", "_ont_source"],
    ) == {
        ("Re9RMq7mRleO0UyLAKpq", "jonathanfemi@example.com", "flyio"),
    }
    assert check_nodes(
        neo4j_session,
        "ComputeInstance",
        ["id", "_ont_name", "_ont_region", "_ont_state", "_ont_source"],
    ) == {
        # "started" (the raw FlyMachine.state, still asserted separately above)
        # normalizes to the shared ComputeInstance canonical state "running".
        (TEST_MACHINE_ID, "dry-rain-8738", "lhr", "running", "flyio"),
    }
    assert check_nodes(
        neo4j_session,
        "BlockStorage",
        [
            "id",
            "_ont_name",
            "_ont_size_gb",
            "_ont_encrypted",
            "_ont_state",
            "_ont_source",
        ],
    ) == {
        # "created" (the raw FlyVolume.state) normalizes to the shared
        # BlockStorage canonical state "available".
        (
            "vol_vlykw0x679gyz5p4",
            "cartography_test_data",
            1,
            True,
            "available",
            "flyio",
        ),
    }
    assert check_nodes(neo4j_session, "Secret", ["id", "_ont_name"]) == {
        (f"{TEST_APP_ID}/SECRET_KEY", "SECRET_KEY"),
        (f"{TEST_APP_ID}/FLY_API_TOKEN", "FLY_API_TOKEN"),
    }
    assert check_nodes(
        neo4j_session,
        "Certificate",
        ["id", "_ont_domain", "_ont_source"],
    ) == {
        (f"{TEST_APP_ID}/www.example.com", "www.example.com", "flyio"),
    }
    assert check_nodes(
        neo4j_session,
        "FlyMachineService",
        ["id", "protocol", "internal_port"],
    ) == {
        (TEST_SERVICE_ID, "tcp", 8000),
    }
    service_ports = neo4j_session.run(
        """
        MATCH (p:FlyMachineServicePort)
        RETURN p.id AS id,
               p.port AS port,
               p.handlers AS handlers,
               p.force_https AS force_https
        ORDER BY port
        """,
    )
    assert [dict(port) for port in service_ports] == [
        {
            "id": f"{TEST_SERVICE_ID}/80",
            "port": 80,
            "handlers": ["http"],
            "force_https": True,
        },
        {
            "id": f"{TEST_SERVICE_ID}/443",
            "port": 443,
            "handlers": ["http", "tls"],
            "force_https": None,
        },
    ]

    assert check_rels(
        neo4j_session,
        "FlyApp",
        "id",
        "FlyOrganization",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {
        (TEST_APP_ID, TEST_ORG_SLUG),
    }
    assert check_rels(
        neo4j_session,
        "FlyMachine",
        "id",
        "FlyApp",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {
        (TEST_MACHINE_ID, TEST_APP_ID),
    }
    assert check_rels(
        neo4j_session,
        "FlyUser",
        "id",
        "FlyOrganization",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {
        ("Re9RMq7mRleO0UyLAKpq", TEST_ORG_SLUG),
    }
    membership = neo4j_session.run(
        """
        MATCH (:FlyUser {id: $user_id})-[r:MEMBER_OF]->
              (:FlyOrganization {id: $org_id})
        RETURN r.role AS role, r.joined_at AS joined_at
        """,
        user_id="Re9RMq7mRleO0UyLAKpq",
        org_id=TEST_ORG_SLUG,
    ).single()
    assert membership is not None
    assert membership["role"] == "ADMIN"
    assert membership["joined_at"] == "2025-02-21T17:12:43Z"
    assert check_rels(
        neo4j_session,
        "FlyUser",
        "id",
        "FlyOrganization",
        "id",
        "MEMBER_OF",
    ) == {
        ("Re9RMq7mRleO0UyLAKpq", TEST_ORG_SLUG),
    }
    assert check_rels(
        neo4j_session,
        "FlyAccessToken",
        "id",
        "FlyOrganization",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {
        ("app_token_active", TEST_ORG_SLUG),
        ("org_token_active", TEST_ORG_SLUG),
    }
    assert check_rels(
        neo4j_session,
        "FlyAccessToken",
        "id",
        "FlyApp",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {
        ("app_token_active", TEST_APP_ID),
        ("app_token_revoked", TEST_APP_ID),
    }
    assert check_rels(
        neo4j_session,
        "FlyAccessToken",
        "id",
        "FlyUser",
        "id",
        "CREATED_BY",
    ) == {
        ("app_token_active", "Re9RMq7mRleO0UyLAKpq"),
        ("app_token_revoked", "Re9RMq7mRleO0UyLAKpq"),
        ("org_token_active", "Re9RMq7mRleO0UyLAKpq"),
    }
    assert check_rels(
        neo4j_session,
        "FlyIP",
        "id",
        "FlyApp",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {
        ("ip_v6_id", TEST_APP_ID),
        ("ip_private_v6_id", TEST_APP_ID),
        (f"{TEST_APP_ID}/66.241.124.236", TEST_APP_ID),
        ("egress_v4_id", TEST_APP_ID),
    }
    assert check_rels(
        neo4j_session,
        "FlyRelease",
        "id",
        "FlyApp",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {
        ("YgoYklRLL8Xo3fBPg6AoX28AG", TEST_APP_ID),
        ("release_previous", TEST_APP_ID),
    }
    assert check_rels(
        neo4j_session,
        "FlyMachine",
        "id",
        "FlyRelease",
        "id",
        "DEPLOYED_FROM",
    ) == {
        (TEST_MACHINE_ID, "YgoYklRLL8Xo3fBPg6AoX28AG"),
    }
    assert check_nodes(
        neo4j_session,
        "Image",
        ["id", "digest", "registry", "repository", "tag", "_ont_digest"],
    ) == {
        (
            TEST_IMAGE_ID,
            TEST_IMAGE_DIGEST,
            "registry.fly.io",
            "nhmhvxo3b9",
            "deployment-01JMWNHS84ZCCV89XYH9SQ48FX",
            TEST_IMAGE_DIGEST,
        ),
    }
    assert check_rels(
        neo4j_session,
        "FlyImage",
        "id",
        "FlyApp",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {
        (TEST_IMAGE_ID, TEST_APP_ID),
    }
    assert check_rels(
        neo4j_session,
        "FlyMachine",
        "id",
        "FlyImage",
        "id",
        "HAS_IMAGE",
    ) == {
        (TEST_MACHINE_ID, TEST_IMAGE_ID),
    }
    assert check_rels(
        neo4j_session,
        "FlyVolume",
        "id",
        "FlyMachine",
        "id",
        "MOUNTS",
        rel_direction_right=False,
    ) == {
        ("vol_vlykw0x679gyz5p4", TEST_MACHINE_ID),
    }
    assert check_rels(
        neo4j_session,
        "FlyMachineService",
        "id",
        "FlyMachine",
        "id",
        "EXPOSE",
        rel_direction_right=False,
    ) == {
        (TEST_SERVICE_ID, TEST_MACHINE_ID),
    }
    assert check_rels(
        neo4j_session,
        "FlyMachineServicePort",
        "id",
        "FlyMachineService",
        "id",
        "EXPOSE",
        rel_direction_right=False,
    ) == {
        (f"{TEST_SERVICE_ID}/80", TEST_SERVICE_ID),
        (f"{TEST_SERVICE_ID}/443", TEST_SERVICE_ID),
    }


def _minimal_machine(machine_id: str, digest: str) -> dict:
    return {
        "id": machine_id,
        "name": machine_id,
        "state": "started",
        "region": "lhr",
        "instance_id": f"{machine_id}-instance",
        "private_ip": "fdaa:10:e286:a7b:34e:c803:57c:9",
        "config": {"guest": {}, "restart": {}, "metadata": {}, "services": []},
        "image_ref": {
            "registry": "registry.fly.io",
            "repository": "shared-repo",
            "tag": "latest",
            "digest": digest,
        },
        "created_at": "2026-08-01T00:00:00Z",
        "updated_at": "2026-08-01T00:00:00Z",
        "host_status": "ok",
        "cordoned": False,
    }


def test_flyio_image_is_scoped_per_app_not_shared_across_apps(neo4j_session):
    """
    Two different apps deploying the exact same image digest must not collapse
    onto one FlyImage node, and each app's Machine must link (HAS_IMAGE) only to
    its own app's image - not to the other app's image node sharing that digest.
    This is a regression test for a bug where FlyImage was keyed purely by
    digest while its cleanup stayed app-scoped, and the HAS_IMAGE matcher
    matched on that non-unique digest.
    """
    # Arrange
    shared_digest = (
        "sha256:cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc"
    )
    load(
        neo4j_session,
        FlyAppSchema(),
        [{"id": "app-a", "name": "app-a"}],
        lastupdated=TEST_UPDATE_TAG,
        ORGANIZATION_ID="org-x",
    )
    load(
        neo4j_session,
        FlyAppSchema(),
        [{"id": "app-b", "name": "app-b"}],
        lastupdated=TEST_UPDATE_TAG,
        ORGANIZATION_ID="org-x",
    )

    # Act: sync app-a and app-b, each with one Machine sharing the same digest.
    with patch.object(
        cartography.intel.flyio.machines,
        "get",
        return_value=[_minimal_machine("machine-a", shared_digest)],
    ):
        cartography.intel.flyio.machines.sync(
            neo4j_session,
            Mock(),
            {
                "BASE_URL": "https://api.machines.dev",
                "APP_NAME": "app-a",
                "APP_ID": "app-a",
                "UPDATE_TAG": TEST_UPDATE_TAG,
            },
        )
    with patch.object(
        cartography.intel.flyio.machines,
        "get",
        return_value=[_minimal_machine("machine-b", shared_digest)],
    ):
        cartography.intel.flyio.machines.sync(
            neo4j_session,
            Mock(),
            {
                "BASE_URL": "https://api.machines.dev",
                "APP_NAME": "app-b",
                "APP_ID": "app-b",
                "UPDATE_TAG": TEST_UPDATE_TAG,
            },
        )

    # Assert: two distinct app-scoped FlyImage nodes, not one shared node.
    # Filtered to this test's own ids (exact, not subset) rather than asserting
    # over the whole label: this file's neo4j_session fixture is module-scoped
    # and shared with test_start_flyio_ingestion above, and filtering our own
    # rows out lets this stay exact without hardcoding that other test's ids
    # (and thus without depending on test execution order between the two).
    all_images = check_nodes(neo4j_session, "FlyImage", ["id", "digest"])
    our_images = {row for row in all_images if row[0].startswith(("app-a/", "app-b/"))}
    assert our_images == {
        (f"app-a/{shared_digest}", shared_digest),
        (f"app-b/{shared_digest}", shared_digest),
    }

    # Assert: each Machine links HAS_IMAGE to exactly its own app's image - no
    # cross-linking to the other app's image node sharing the same digest, and
    # no unexpected extra edges from either machine.
    all_has_image = check_rels(
        neo4j_session,
        "FlyMachine",
        "id",
        "FlyImage",
        "id",
        "HAS_IMAGE",
    )
    our_has_image = {
        row for row in all_has_image if row[0] in ("machine-a", "machine-b")
    }
    assert our_has_image == {
        ("machine-a", f"app-a/{shared_digest}"),
        ("machine-b", f"app-b/{shared_digest}"),
    }
