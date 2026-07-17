from unittest.mock import Mock
from unittest.mock import patch

import pytest
import requests

import cartography.intel.databricks.grants
import cartography.intel.databricks.groups
import cartography.intel.databricks.service_principals
import cartography.intel.databricks.tables
import cartography.intel.databricks.users
from tests.data.databricks.grants import DATABRICKS_GRANTS
from tests.data.databricks.groups import DATABRICKS_GROUPS
from tests.data.databricks.metastore import DATABRICKS_METASTORE_ID
from tests.data.databricks.service_principals import DATABRICKS_SERVICE_PRINCIPALS
from tests.data.databricks.tables import DATABRICKS_TABLES
from tests.data.databricks.users import DATABRICKS_USERS
from tests.data.databricks.workspace import DATABRICKS_WORKSPACE_ID
from tests.integration.cartography.intel.databricks.test_catalogs import (
    _ensure_local_neo4j_has_test_catalogs,
)
from tests.integration.cartography.intel.databricks.test_metastores import (
    _ensure_local_neo4j_has_test_metastore,
)
from tests.integration.cartography.intel.databricks.test_schemas import (
    _ensure_local_neo4j_has_test_schemas,
)
from tests.integration.cartography.intel.databricks.test_workspaces import (
    _ensure_local_neo4j_has_test_workspace,
)
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789


def _uc_id(full_name):
    return f"{DATABRICKS_METASTORE_ID}/{full_name}"


def _seed_principals(neo4j_session):
    cartography.intel.databricks.users.load_users(
        neo4j_session,
        cartography.intel.databricks.users.transform(
            DATABRICKS_USERS, DATABRICKS_WORKSPACE_ID
        ),
        DATABRICKS_WORKSPACE_ID,
        TEST_UPDATE_TAG,
    )
    cartography.intel.databricks.groups.load_groups(
        neo4j_session,
        cartography.intel.databricks.groups.transform(
            DATABRICKS_GROUPS, DATABRICKS_WORKSPACE_ID
        ),
        DATABRICKS_WORKSPACE_ID,
        TEST_UPDATE_TAG,
    )
    cartography.intel.databricks.service_principals.load_service_principals(
        neo4j_session,
        cartography.intel.databricks.service_principals.transform(
            DATABRICKS_SERVICE_PRINCIPALS, DATABRICKS_WORKSPACE_ID
        ),
        DATABRICKS_WORKSPACE_ID,
        TEST_UPDATE_TAG,
    )


def _seed_tables(neo4j_session):
    cartography.intel.databricks.tables.load_tables(
        neo4j_session,
        cartography.intel.databricks.tables.transform(DATABRICKS_TABLES),
        DATABRICKS_WORKSPACE_ID,
        TEST_UPDATE_TAG,
    )


@patch.object(
    cartography.intel.databricks.grants,
    "get",
    return_value=(DATABRICKS_GRANTS, True),
)
def test_load_databricks_grants(mock_get, neo4j_session):
    api_session = Mock()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "WORKSPACE_ID": DATABRICKS_WORKSPACE_ID,
    }
    _ensure_local_neo4j_has_test_workspace(neo4j_session)
    _ensure_local_neo4j_has_test_metastore(neo4j_session)
    _ensure_local_neo4j_has_test_catalogs(neo4j_session)
    _ensure_local_neo4j_has_test_schemas(neo4j_session)
    _seed_tables(neo4j_session)
    _seed_principals(neo4j_session)

    cartography.intel.databricks.grants.sync(
        neo4j_session,
        api_session,
        DATABRICKS_WORKSPACE_ID,
        common_job_parameters,
    )

    # User -> Catalog HAS_PRIVILEGE
    assert check_rels(
        neo4j_session,
        "DatabricksUser",
        "user_name",
        "DatabricksCatalog",
        "id",
        "HAS_PRIVILEGE",
        rel_direction_right=True,
    ) == {("jeremy@subimage.io", _uc_id("prod"))}

    # Group -> Table HAS_PRIVILEGE
    assert check_rels(
        neo4j_session,
        "DatabricksGroup",
        "display_name",
        "DatabricksTable",
        "id",
        "HAS_PRIVILEGE",
        rel_direction_right=True,
    ) == {("admins", _uc_id("prod.finance.customers"))}

    # ServicePrincipal -> Schema HAS_PRIVILEGE
    assert check_rels(
        neo4j_session,
        "DatabricksServicePrincipal",
        "application_id",
        "DatabricksSchema",
        "id",
        "HAS_PRIVILEGE",
        rel_direction_right=True,
    ) == {("abcd1234-5678-90ab-cdef-1234567890ab", _uc_id("prod.finance"))}


def _http_error(status_code):
    response = Mock(spec=requests.Response)
    response.status_code = status_code
    return requests.HTTPError(response=response)


def test_grants_get_skips_system_registered_model_keeps_complete():
    """A 400 on a `system`-catalog registered_model is the known non-grantable
    case: it is skipped, the remaining securables still load their grants, and
    the read stays complete (it has no HAS_PRIVILEGE edges, so cleanup may run)."""
    securables = [
        {
            "id": _uc_id("system.ai.model"),
            "full_name": "system.ai.model",
            "securable_type": "registered_model",
        },
        {
            "id": _uc_id("prod"),
            "full_name": "prod",
            "securable_type": "catalog",
        },
    ]
    api_session = Mock()
    api_session.uc_list.side_effect = [
        _http_error(400),
        [{"principal": "jeremy@subimage.io", "privileges": ["USE_CATALOG"]}],
    ]

    grants, complete = cartography.intel.databricks.grants.get(api_session, securables)

    assert complete is True
    assert grants == [
        {
            "principal": "jeremy@subimage.io",
            "securable_id": _uc_id("prod"),
            "privileges": ["USE_CATALOG"],
        }
    ]


def test_grants_get_unexpected_400_propagates():
    """A 400 on a securable that is NOT the known non-grantable case (e.g. a
    real catalog that may already hold grants) is a genuine BAD_REQUEST: it must
    abort rather than be swallowed and silently disable cleanup."""
    securables = [
        {
            "id": _uc_id("prod"),
            "full_name": "prod",
            "securable_type": "catalog",
        },
    ]
    api_session = Mock()
    api_session.uc_list.side_effect = _http_error(400)

    with pytest.raises(requests.HTTPError):
        cartography.intel.databricks.grants.get(api_session, securables)


def test_grants_get_forbidden_securable_flags_incomplete():
    """A 403/404 securable may hold grants we could not read, so the read is
    flagged incomplete (so the caller skips cleanup) while the remaining
    securables still load their grants."""
    securables = [
        {
            "id": _uc_id("locked"),
            "full_name": "locked",
            "securable_type": "catalog",
        },
        {
            "id": _uc_id("prod"),
            "full_name": "prod",
            "securable_type": "catalog",
        },
    ]
    api_session = Mock()
    api_session.uc_list.side_effect = [
        _http_error(403),
        [{"principal": "jeremy@subimage.io", "privileges": ["USE_CATALOG"]}],
    ]

    grants, complete = cartography.intel.databricks.grants.get(api_session, securables)

    assert complete is False
    assert grants == [
        {
            "principal": "jeremy@subimage.io",
            "securable_id": _uc_id("prod"),
            "privileges": ["USE_CATALOG"],
        }
    ]


def test_grants_get_other_http_error_propagates():
    """A non-skippable status (e.g. 500) must abort so cleanup never runs on
    partial data."""
    securables = [
        {
            "id": _uc_id("prod"),
            "full_name": "prod",
            "securable_type": "catalog",
        },
    ]
    api_session = Mock()
    api_session.uc_list.side_effect = _http_error(500)

    with pytest.raises(requests.HTTPError):
        cartography.intel.databricks.grants.get(api_session, securables)
