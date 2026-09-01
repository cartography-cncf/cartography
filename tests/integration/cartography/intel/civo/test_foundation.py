import importlib
import pkgutil
from contextlib import ExitStack
from types import ModuleType
from unittest.mock import patch

import pytest
import requests

import cartography.intel.civo
import cartography.intel.civo.account
import cartography.intel.civo.sshkeys
from cartography.config import Config
from tests.data.civo.account import QUOTA_RESPONSE
from tests.data.civo.sshkeys import SSH_KEYS_RESPONSE
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_BASE_URL = "https://api.fake-civo.com"
TEST_ACCOUNT_ID = QUOTA_RESPONSE["id"]
TEST_REGION_CODE = "lon1"


def _common_job_parameters() -> dict:
    return {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "BASE_URL": TEST_BASE_URL,
        # Only one region in tests: every regional get() is mocked directly
        # (get()/get_stores()/etc.), so the fan-out helpers themselves aren't
        # exercised here - see test_civo.py (unit) for that. One entry, with
        # every feature flag on, is enough to prove the region-scoped call
        # chain is wired correctly regardless of which feature a module
        # filters on.
        "REGIONS": [
            {
                "code": TEST_REGION_CODE,
                "features": {
                    "iaas": True,
                    "kubernetes": True,
                    "object_store": True,
                    "loadbalancer": True,
                    "gpu": True,
                    "dbaas": True,
                    "volume": True,
                    "paas": True,
                    "public_ip_node_pools": True,
                },
            },
        ],
    }


@patch.object(
    cartography.intel.civo.sshkeys,
    "get",
    return_value=SSH_KEYS_RESPONSE,
)
@patch.object(
    cartography.intel.civo.account,
    "get",
    return_value=QUOTA_RESPONSE,
)
def test_civo_account_and_sshkeys_sync(
    mock_account_get, mock_sshkeys_get, neo4j_session
):
    # Arrange
    api_session = requests.Session()
    common_job_parameters = _common_job_parameters()

    # Act: sync the account (tenant) first, then the account-scoped ssh keys,
    # mirroring cartography.intel.civo.start_civo_ingestion's phase order.
    account = cartography.intel.civo.account.sync(
        neo4j_session,
        api_session,
        common_job_parameters,
    )
    common_job_parameters["ACCOUNT_ID"] = account["id"]
    cartography.intel.civo.sshkeys.sync(
        neo4j_session,
        api_session,
        common_job_parameters,
    )

    # Assert: CivoAccount loaded correctly.
    assert check_nodes(
        neo4j_session,
        "CivoAccount",
        ["id", "default_user_id", "default_user_email_address"],
    ) == {
        (
            QUOTA_RESPONSE["id"],
            QUOTA_RESPONSE["default_user_id"],
            QUOTA_RESPONSE["default_user_email_address"],
        ),
    }

    # Assert: all SSH keys across both pages loaded, with fingerprints intact.
    assert check_nodes(
        neo4j_session,
        "CivoSSHKey",
        ["id", "name", "fingerprint"],
    ) == {(key["id"], key["name"], key["fingerprint"]) for key in SSH_KEYS_RESPONSE}

    # Assert: every SSH key is scoped to the account.
    assert check_rels(
        neo4j_session,
        "CivoSSHKey",
        "id",
        "CivoAccount",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {(key["id"], TEST_ACCOUNT_ID) for key in SSH_KEYS_RESPONSE}


@patch.object(
    cartography.intel.civo.sshkeys,
    "get",
)
@patch.object(
    cartography.intel.civo.account,
    "get",
    return_value=QUOTA_RESPONSE,
)
def test_civo_sshkey_cleanup_removes_stale_keys(
    mock_account_get, mock_sshkeys_get, neo4j_session
):
    # Arrange: one full sync with two keys.
    api_session = requests.Session()
    common_job_parameters = _common_job_parameters()
    mock_sshkeys_get.return_value = SSH_KEYS_RESPONSE
    account = cartography.intel.civo.account.sync(
        neo4j_session,
        api_session,
        common_job_parameters,
    )
    common_job_parameters["ACCOUNT_ID"] = account["id"]
    cartography.intel.civo.sshkeys.sync(
        neo4j_session,
        api_session,
        common_job_parameters,
    )
    # sync() no longer runs cleanup() itself (see start_civo_ingestion's
    # Phase 3 comment) - the real entrypoint runs it once at the very end,
    # so tests that want to exercise it call it explicitly.
    cartography.intel.civo.sshkeys.cleanup(neo4j_session, common_job_parameters)

    # Act: re-sync with one key removed upstream, under a new update tag.
    mock_sshkeys_get.return_value = SSH_KEYS_RESPONSE[:1]
    common_job_parameters["UPDATE_TAG"] = TEST_UPDATE_TAG + 1
    cartography.intel.civo.sshkeys.sync(
        neo4j_session,
        api_session,
        common_job_parameters,
    )
    cartography.intel.civo.sshkeys.cleanup(neo4j_session, common_job_parameters)

    # Assert: only the still-present key remains.
    assert check_nodes(neo4j_session, "CivoSSHKey", ["id"]) == {
        (SSH_KEYS_RESPONSE[0]["id"],),
    }


def _discover_sync_modules() -> dict[str, ModuleType]:
    modules = {}
    for module_info in pkgutil.iter_modules(cartography.intel.civo.__path__):
        module = importlib.import_module(
            f"{cartography.intel.civo.__name__}.{module_info.name}",
        )
        if hasattr(module, "sync") and hasattr(module, "cleanup"):
            modules[module_info.name] = module
    return modules


def test_start_civo_ingestion_wires_every_available_module(neo4j_session):
    """
    Exercise the real entrypoint while adapting to every Civo module present
    on the current stacked branch. Discovering modules from package files,
    rather than from __init__.py's imports, catches both a missing import and
    a missing sync/cleanup call without allowing any HTTP request.
    """
    # Arrange
    config = Config(
        neo4j_uri="bolt://fake-neo4j:7687",
        update_tag=TEST_UPDATE_TAG,
        civo_api_key="fake-key",
        civo_base_url=TEST_BASE_URL,
    )

    modules = _discover_sync_modules()
    assert {"account", "sshkeys"} <= set(modules)

    with ExitStack() as stack:
        sync_mocks = {}
        cleanup_mocks = {}
        for name, module in modules.items():
            return_value = QUOTA_RESPONSE if name == "account" else None
            sync_mocks[name] = stack.enter_context(
                patch.object(module, "sync", return_value=return_value),
            )
            cleanup_mocks[name] = stack.enter_context(patch.object(module, "cleanup"))
        stack.enter_context(
            patch.object(
                cartography.intel.civo,
                "get_regions",
                return_value=[],
                create=True,
            ),
        )

        # Act
        cartography.intel.civo.start_civo_ingestion(neo4j_session, config)

    # Assert: every module file with the sync contract is wired into both
    # entrypoint phases. Domain tests cover each implementation's graph output.
    for module_mock in sync_mocks.values():
        module_mock.assert_called_once()
    for module_mock in cleanup_mocks.values():
        module_mock.assert_called_once()


def test_start_civo_ingestion_defaults_base_url_for_programmatic_config(
    neo4j_session,
):
    """
    Config defaults civo_base_url to None; the CLI supplies the default, but
    programmatic callers should still get the documented API base URL.
    """
    # Arrange
    config = Config(
        neo4j_uri="bolt://fake-neo4j:7687",
        update_tag=TEST_UPDATE_TAG,
        civo_api_key="fake-key",
        civo_base_url=None,
    )

    modules = _discover_sync_modules()
    assert {"account", "sshkeys"} <= set(modules)

    with ExitStack() as stack:
        sync_mocks = {}
        cleanup_mocks = {}
        for name, module in modules.items():
            return_value = QUOTA_RESPONSE if name == "account" else None
            sync_mocks[name] = stack.enter_context(
                patch.object(module, "sync", return_value=return_value),
            )
            cleanup_mocks[name] = stack.enter_context(patch.object(module, "cleanup"))
        stack.enter_context(
            patch.object(
                cartography.intel.civo,
                "get_regions",
                return_value=[],
                create=True,
            ),
        )

        # Act
        cartography.intel.civo.start_civo_ingestion(neo4j_session, config)

    # Assert
    account_parameters = sync_mocks["account"].call_args.args[2]
    assert account_parameters["BASE_URL"] == "https://api.civo.com"


def test_start_civo_ingestion_failure_skips_every_cleanup(neo4j_session):
    """A failed load must abort before cleanup for every available module."""
    config = Config(
        neo4j_uri="bolt://fake-neo4j:7687",
        update_tag=TEST_UPDATE_TAG,
        civo_api_key="fake-key",
        civo_base_url=TEST_BASE_URL,
    )
    modules = _discover_sync_modules()

    with ExitStack() as stack:
        sync_mocks = {}
        cleanup_mocks = {}
        for name, module in modules.items():
            return_value = QUOTA_RESPONSE if name == "account" else None
            sync_mocks[name] = stack.enter_context(
                patch.object(module, "sync", return_value=return_value),
            )
            cleanup_mocks[name] = stack.enter_context(patch.object(module, "cleanup"))
        stack.enter_context(
            patch.object(
                cartography.intel.civo,
                "get_regions",
                return_value=[],
                create=True,
            ),
        )
        sync_mocks["sshkeys"].side_effect = RuntimeError("simulated upstream failure")

        with pytest.raises(RuntimeError, match="simulated upstream failure"):
            cartography.intel.civo.start_civo_ingestion(neo4j_session, config)

    for module_mock in cleanup_mocks.values():
        module_mock.assert_not_called()


def test_start_civo_ingestion_skips_when_unconfigured(neo4j_session):
    """
    Config-gating only: safe regardless of how much the entrypoint grows,
    since `civo_api_key=None` returns before calling anything.
    """
    # Arrange: no civo_api_key - the entrypoint must skip entirely, not
    # raise or make any API call. Snapshot CivoAccount before acting, not
    # an assumed-empty set: an earlier test in this module-scoped session
    # (test_civo_account_and_sshkeys_sync) legitimately leaves its own
    # CivoAccount node behind (CivoAccountSchema has no cleanup of its
    # own - see start_civo_ingestion's Phase 3 comment).
    config = Config(
        neo4j_uri="bolt://fake-neo4j:7687",
        update_tag=TEST_UPDATE_TAG,
        civo_api_key=None,
        civo_base_url=TEST_BASE_URL,
    )
    before = check_nodes(neo4j_session, "CivoAccount", ["id"])

    # Act
    cartography.intel.civo.start_civo_ingestion(neo4j_session, config)

    # Assert: nothing new was loaded.
    assert check_nodes(neo4j_session, "CivoAccount", ["id"]) == before
