import asyncio
from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.modal.dicts
import cartography.intel.modal.domains
import cartography.intel.modal.environments
import cartography.intel.modal.nfs
import cartography.intel.modal.proxies
import cartography.intel.modal.queues
import cartography.intel.modal.secrets
import cartography.intel.modal.volumes
import tests.data.modal.storage as fx
from tests.integration.cartography.intel.modal.test_environments import (
    _ensure_local_neo4j_has_test_environments,
)
from tests.integration.cartography.intel.modal.test_identity import (
    _ensure_local_neo4j_has_test_members,
)
from tests.integration.cartography.intel.modal.test_workspace import (
    _ensure_local_neo4j_has_test_workspace,
)
from tests.integration.cartography.intel.modal.test_workspace import TEST_UPDATE_TAG
from tests.integration.cartography.intel.modal.test_workspace import TEST_WORKSPACE_ID
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_ENVIRONMENT_ID = "en-C3umado26sLFrhYfZjoWjL"
TEST_ENVIRONMENT_NAME = "main"


def _params(update_tag=TEST_UPDATE_TAG):
    return {
        "UPDATE_TAG": update_tag,
        "WORKSPACE_ID": TEST_WORKSPACE_ID,
        "ENVIRONMENT_ID": TEST_ENVIRONMENT_ID,
        "ENVIRONMENT_NAME": TEST_ENVIRONMENT_NAME,
    }


def _seed(neo4j_session):
    _ensure_local_neo4j_has_test_workspace(neo4j_session)
    _ensure_local_neo4j_has_test_environments(neo4j_session)


def _run_sync(module, getter, fixture, update_tag=TEST_UPDATE_TAG, extra=()):
    """Run one resource sync with its getter mocked.

    `extra` carries the trailing arguments only some syncs take: secrets and volumes receive
    the workspace's {username: user_id} map so they can attribute creation.
    """

    def _inner(neo4j_session):
        with patch.object(module, getter, return_value=fixture):
            return asyncio.run(
                module.sync(neo4j_session, MagicMock(), _params(update_tag), *extra)
            )

    return _inner


def test_load_modal_secrets(neo4j_session):
    # Arrange
    _seed(neo4j_session)
    usernames = _ensure_local_neo4j_has_test_members(neo4j_session)

    # Act
    _run_sync(
        cartography.intel.modal.secrets,
        "list_secrets",
        fx.MODAL_SECRETS,
        extra=(usernames,),
    )(neo4j_session)

    # Assert
    assert check_nodes(neo4j_session, "ModalSecret", ["id", "name"]) == {
        ("st-poEHPwc7kwkkLwrnaVPjTn", "e2e-secret"),
        ("st-2XbNmQwErTyUiOpAsDfGh", "prod-db-password"),
    }
    # last_used_at is the only signal that a secret is still in use, since which workloads
    # consume it is not readable. Null for a never-read secret, set for a used one.
    used = {
        (r["name"], r["last_used_at"] is not None)
        for r in neo4j_session.run(
            "MATCH (s:ModalSecret) RETURN s.name AS name, s.last_used_at AS last_used_at"
        )
    }
    assert used == {("e2e-secret", False), ("prod-db-password", True)}
    assert check_rels(
        neo4j_session,
        "ModalSecret",
        "id",
        "ModalEnvironment",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {
        ("st-poEHPwc7kwkkLwrnaVPjTn", TEST_ENVIRONMENT_ID),
        ("st-2XbNmQwErTyUiOpAsDfGh", TEST_ENVIRONMENT_ID),
    }
    # CREATED_BY joins on display_name, and only resolves for a member that exists.
    assert check_rels(
        neo4j_session,
        "ModalSecret",
        "name",
        "ModalUser",
        "display_name",
        "CREATED_BY",
    ) == {("e2e-secret", "alice")}


def test_modal_secret_stores_no_value(neo4j_session):
    """Modal returns no secret values through any read API, so no property may carry one."""
    # Arrange
    _seed(neo4j_session)

    # Act
    _run_sync(
        cartography.intel.modal.secrets, "list_secrets", fx.MODAL_SECRETS, extra=({},)
    )(neo4j_session)

    # Assert
    keys = set()
    for record in neo4j_session.run("MATCH (s:ModalSecret) RETURN keys(s) AS ks"):
        keys.update(record["ks"])
    assert not {k for k in keys if k in {"value", "values", "env_dict", "data"}}


def test_load_modal_volumes_and_nfs(neo4j_session):
    # Arrange
    _seed(neo4j_session)
    usernames = _ensure_local_neo4j_has_test_members(neo4j_session)

    # Act
    _run_sync(
        cartography.intel.modal.volumes,
        "list_volumes",
        fx.MODAL_VOLUMES,
        extra=(usernames,),
    )(neo4j_session)
    _run_sync(cartography.intel.modal.nfs, "list_nfs", fx.MODAL_NETWORK_FILE_SYSTEMS)(
        neo4j_session
    )

    # Assert
    assert check_nodes(neo4j_session, "ModalVolume", ["name", "version"]) == {
        ("e2e-volume", "VOLUME_FS_VERSION_V1"),
        ("model-weights", "VOLUME_FS_VERSION_V2"),
    }
    assert check_nodes(
        neo4j_session, "ModalNetworkFileSystem", ["name", "cloud_provider"]
    ) == {("legacy-share", "CLOUD_PROVIDER_AWS")}
    assert check_rels(
        neo4j_session,
        "ModalVolume",
        "name",
        "ModalUser",
        "display_name",
        "CREATED_BY",
    ) == {("e2e-volume", "alice"), ("model-weights", "bob")}


def test_modal_storage_ontology_filestorage_mapping(neo4j_session):
    """Both volume kinds must surface as FileStorage with a normalised name."""
    # Arrange
    _seed(neo4j_session)

    # Act
    _run_sync(
        cartography.intel.modal.volumes, "list_volumes", fx.MODAL_VOLUMES, extra=({},)
    )(neo4j_session)
    _run_sync(cartography.intel.modal.nfs, "list_nfs", fx.MODAL_NETWORK_FILE_SYSTEMS)(
        neo4j_session
    )

    # Assert
    # labels() order is not guaranteed, so pick the Modal label explicitly rather than
    # indexing into it.
    rows = {
        (r["provider_label"], r["name"])
        for r in neo4j_session.run(
            """
            MATCH (n:FileStorage)
            WHERE any(l IN labels(n) WHERE l STARTS WITH 'Modal')
            RETURN [l IN labels(n) WHERE l STARTS WITH 'Modal'][0] AS provider_label,
                   n._ont_name AS name
            """
        )
    }
    assert rows == {
        ("ModalVolume", "e2e-volume"),
        ("ModalVolume", "model-weights"),
        ("ModalNetworkFileSystem", "legacy-share"),
    }


def test_load_modal_dicts_and_queues(neo4j_session):
    # Arrange
    _seed(neo4j_session)

    # Act
    _run_sync(cartography.intel.modal.dicts, "list_dicts", fx.MODAL_DICTS)(
        neo4j_session
    )
    _run_sync(cartography.intel.modal.queues, "list_queues", fx.MODAL_QUEUES)(
        neo4j_session
    )

    # Assert
    assert check_nodes(neo4j_session, "ModalDict", ["id", "name"]) == {
        ("di-F91whmwZVRH92mOiJgNOCT", "e2e-dict"),
    }
    assert check_nodes(neo4j_session, "ModalQueue", ["id", "name"]) == {
        ("qu-kbM1N097wnpOSJgRjiwXvk", "e2e-queue"),
    }
    for label in ("ModalDict", "ModalQueue"):
        assert check_rels(
            neo4j_session,
            label,
            "id",
            "ModalEnvironment",
            "id",
            "RESOURCE",
            rel_direction_right=False,
        )


def test_load_modal_domains_and_dns_records(neo4j_session):
    # Arrange
    _seed(neo4j_session)

    # Act
    with patch.object(
        cartography.intel.modal.domains,
        "list_domains",
        return_value=(fx.MODAL_DOMAINS, True),
    ):
        asyncio.run(
            cartography.intel.modal.domains.sync(
                neo4j_session,
                MagicMock(),
                {"UPDATE_TAG": TEST_UPDATE_TAG, "WORKSPACE_ID": TEST_WORKSPACE_ID},
            )
        )

    # Assert
    assert check_nodes(
        neo4j_session, "ModalDomain", ["domain_name", "certificate_status"]
    ) == {
        ("api.example.com", "CERTIFICATE_STATUS_ISSUED"),
        ("broken.example.com", "CERTIFICATE_STATUS_FAILED"),
    }
    assert check_nodes(neo4j_session, "ModalDomainDNSRecord", ["name", "type"]) == {
        ("api.example.com", "DNS_RECORD_TYPE_CNAME"),
        ("_modal-challenge.api.example.com", "DNS_RECORD_TYPE_TXT"),
    }
    assert check_rels(
        neo4j_session,
        "ModalDomain",
        "domain_name",
        "ModalDomainDNSRecord",
        "name",
        "HAS_RECORD",
    ) == {
        ("api.example.com", "api.example.com"),
        ("api.example.com", "_modal-challenge.api.example.com"),
    }
    # Domains are workspace-scoped, not environment-scoped.
    assert check_rels(
        neo4j_session,
        "ModalDomain",
        "domain_name",
        "ModalWorkspace",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {
        ("api.example.com", TEST_WORKSPACE_ID),
        ("broken.example.com", TEST_WORKSPACE_ID),
    }


def test_modal_dns_records_are_not_labelled_dnsrecord(neo4j_session):
    """These are records Modal asks you to create, not observed DNS state, so labelling them
    DNSRecord would feed the DNS linking analysis entries that may not exist anywhere.
    """
    # Arrange
    _seed(neo4j_session)

    # Act
    with patch.object(
        cartography.intel.modal.domains,
        "list_domains",
        return_value=(fx.MODAL_DOMAINS, True),
    ):
        asyncio.run(
            cartography.intel.modal.domains.sync(
                neo4j_session,
                MagicMock(),
                {"UPDATE_TAG": TEST_UPDATE_TAG, "WORKSPACE_ID": TEST_WORKSPACE_ID},
            )
        )

    # Assert
    for record in neo4j_session.run(
        "MATCH (r:ModalDomainDNSRecord) RETURN labels(r) AS labels"
    ):
        assert "DNSRecord" not in set(record["labels"])


def test_load_modal_proxies_filters_by_environment(neo4j_session):
    """ProxyList is workspace-wide, so the per-environment sync must drop other environments'
    proxies rather than attach them here."""
    # Arrange
    _seed(neo4j_session)

    # Act
    # ProxyList is fetched once by the caller now, so the listing is passed in.
    asyncio.run(
        cartography.intel.modal.proxies.sync(
            neo4j_session, MagicMock(), _params(), fx.MODAL_PROXIES
        )
    )

    # Assert
    assert check_nodes(neo4j_session, "ModalProxy", ["name", "region"]) == {
        ("egress-proxy", "us-east-1"),
    }
    assert check_nodes(neo4j_session, "ModalProxyIP", ["ip_address", "status"]) == {
        ("203.0.113.10", "PROXY_IP_STATUS_ONLINE"),
        ("203.0.113.11", "PROXY_IP_STATUS_UNHEALTHY"),
    }
    assert check_rels(
        neo4j_session, "ModalProxy", "name", "ModalProxyIP", "ip_address", "HAS_IP"
    ) == {
        ("egress-proxy", "203.0.113.10"),
        ("egress-proxy", "203.0.113.11"),
    }


def test_removed_environment_cascades_storage_cleanup(neo4j_session):
    """The cascade registry must cover storage and proxies too."""
    # Arrange
    _seed(neo4j_session)
    _run_sync(
        cartography.intel.modal.secrets, "list_secrets", fx.MODAL_SECRETS, extra=({},)
    )(neo4j_session)
    _run_sync(
        cartography.intel.modal.volumes, "list_volumes", fx.MODAL_VOLUMES, extra=({},)
    )(neo4j_session)
    _run_sync(cartography.intel.modal.nfs, "list_nfs", fx.MODAL_NETWORK_FILE_SYSTEMS)(
        neo4j_session
    )
    _run_sync(cartography.intel.modal.dicts, "list_dicts", fx.MODAL_DICTS)(
        neo4j_session
    )
    _run_sync(cartography.intel.modal.queues, "list_queues", fx.MODAL_QUEUES)(
        neo4j_session
    )
    # ProxyList is fetched once by the caller now, so the listing is passed in.
    asyncio.run(
        cartography.intel.modal.proxies.sync(
            neo4j_session, MagicMock(), _params(), fx.MODAL_PROXIES
        )
    )
    labels = (
        "ModalSecret",
        "ModalVolume",
        "ModalNetworkFileSystem",
        "ModalDict",
        "ModalQueue",
        "ModalProxy",
        "ModalProxyIP",
    )
    for label in labels:
        assert check_nodes(neo4j_session, label, ["id"]), f"{label} not seeded"

    # Act
    cartography.intel.modal.environments.cleanup_removed_environments(
        neo4j_session,
        TEST_WORKSPACE_ID,
        live_environment_ids=set(),
        update_tag=TEST_UPDATE_TAG + 1,
    )

    # Assert
    for label in labels:
        assert (
            check_nodes(neo4j_session, label, ["id"]) == set()
        ), f"{label} survived its deleted environment"
