from unittest.mock import Mock
from unittest.mock import patch

import pytest
import requests

import cartography.intel.databricks.clusters
import cartography.intel.databricks.groups
import cartography.intel.databricks.jobs
import cartography.intel.databricks.permissions
import cartography.intel.databricks.secret_scopes
import cartography.intel.databricks.service_principals
import cartography.intel.databricks.users
from tests.data.databricks.clusters import DATABRICKS_CLUSTERS
from tests.data.databricks.groups import DATABRICKS_GROUPS
from tests.data.databricks.jobs import DATABRICKS_JOBS
from tests.data.databricks.permissions import DATABRICKS_PERMISSIONS
from tests.data.databricks.secret_scopes import DATABRICKS_SECRET_SCOPES
from tests.data.databricks.service_principals import DATABRICKS_SERVICE_PRINCIPALS
from tests.data.databricks.users import DATABRICKS_USERS
from tests.data.databricks.workspace import DATABRICKS_WORKSPACE_ID
from tests.data.databricks.workspace import scoped
from tests.integration.cartography.intel.databricks.test_workspaces import (
    _ensure_local_neo4j_has_test_workspace,
)
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789

# The permissions API returns one ACL entry per principal (cluster + job);
# the secret scope ACL comes from the separate secrets endpoint.
_OBJECT_PERMISSIONS = [
    p for p in DATABRICKS_PERMISSIONS if p["object_type"] != "secret-scope"
]
_SECRET_SCOPE_ACLS = [
    p for p in DATABRICKS_PERMISSIONS if p["object_type"] == "secret-scope"
]


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


def _seed_objects(neo4j_session):
    cartography.intel.databricks.clusters.load_clusters(
        neo4j_session,
        cartography.intel.databricks.clusters.transform(
            DATABRICKS_CLUSTERS, DATABRICKS_WORKSPACE_ID
        ),
        DATABRICKS_WORKSPACE_ID,
        TEST_UPDATE_TAG,
    )
    cartography.intel.databricks.jobs.load_jobs(
        neo4j_session,
        cartography.intel.databricks.jobs.transform_jobs(
            DATABRICKS_JOBS, DATABRICKS_WORKSPACE_ID, {}
        ),
        DATABRICKS_WORKSPACE_ID,
        TEST_UPDATE_TAG,
    )
    cartography.intel.databricks.secret_scopes.load_secret_scopes(
        neo4j_session,
        cartography.intel.databricks.secret_scopes.transform(
            DATABRICKS_SECRET_SCOPES, DATABRICKS_WORKSPACE_ID
        ),
        DATABRICKS_WORKSPACE_ID,
        TEST_UPDATE_TAG,
    )


@patch.object(
    cartography.intel.databricks.permissions,
    "get_secret_scope_acls",
    return_value=(_SECRET_SCOPE_ACLS, True),
)
@patch.object(
    cartography.intel.databricks.permissions,
    "get",
    return_value=(_OBJECT_PERMISSIONS, True),
)
def test_load_databricks_permissions(mock_get, mock_scope_acls, neo4j_session):
    api_session = Mock()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "WORKSPACE_ID": DATABRICKS_WORKSPACE_ID,
    }
    _ensure_local_neo4j_has_test_workspace(neo4j_session)
    _seed_principals(neo4j_session)
    _seed_objects(neo4j_session)

    cartography.intel.databricks.permissions.sync(
        neo4j_session,
        api_session,
        DATABRICKS_WORKSPACE_ID,
        common_job_parameters,
    )

    # User -> Cluster HAS_PERMISSION
    assert check_rels(
        neo4j_session,
        "DatabricksUser",
        "user_name",
        "DatabricksCluster",
        "id",
        "HAS_PERMISSION",
        rel_direction_right=True,
    ) == {("jeremy@subimage.io", scoped("0202-cluster-aaaa"))}

    # Group -> Job HAS_PERMISSION
    assert check_rels(
        neo4j_session,
        "DatabricksGroup",
        "display_name",
        "DatabricksJob",
        "id",
        "HAS_PERMISSION",
        rel_direction_right=True,
    ) == {("admins", scoped("1011944831447606"))}

    # ServicePrincipal -> SecretScope HAS_PERMISSION (from the secrets ACL)
    assert check_rels(
        neo4j_session,
        "DatabricksServicePrincipal",
        "application_id",
        "DatabricksSecretScope",
        "id",
        "HAS_PERMISSION",
        rel_direction_right=True,
    ) == {("abcd1234-5678-90ab-cdef-1234567890ab", scoped("ci-cd"))}


def _http_error(status_code):
    response = Mock(spec=requests.Response)
    response.status_code = status_code
    return requests.HTTPError(response=response)


def test_permissions_get_skips_ineligible_object():
    """A 400 on a structurally-ineligible object is skipped (and flags the read
    incomplete so cleanup is skipped); other objects still load their ACLs."""
    objects = [
        {"id": scoped("bad"), "object_type": "clusters", "object_ref": "bad"},
        {"id": scoped("good"), "object_type": "clusters", "object_ref": "good"},
    ]
    api_session = Mock()
    api_session.get.side_effect = [
        _http_error(400),
        {
            "access_control_list": [
                {
                    "user_name": "jeremy@subimage.io",
                    "all_permissions": [{"permission_level": "CAN_MANAGE"}],
                }
            ]
        },
    ]

    permissions, complete = cartography.intel.databricks.permissions.get(
        api_session, objects
    )

    assert complete is False
    assert permissions == [
        {
            "principal": "jeremy@subimage.io",
            "object_id": scoped("good"),
            "permission_level": ["CAN_MANAGE"],
            "object_type": "clusters",
        }
    ]


def test_permissions_get_other_http_error_propagates():
    """A non-skippable status (e.g. 500) must abort so cleanup never runs on
    partial data."""
    objects = [
        {"id": scoped("good"), "object_type": "clusters", "object_ref": "good"},
    ]
    api_session = Mock()
    api_session.get.side_effect = _http_error(500)

    with pytest.raises(requests.HTTPError):
        cartography.intel.databricks.permissions.get(api_session, objects)


def test_get_secret_scope_acls_skips_ineligible_scope():
    """A 400 on a secret scope ACL is skipped (and flags the read incomplete);
    the remaining scopes still load their ACLs."""
    scopes = [
        {"id": scoped("bad"), "name": "bad"},
        {"id": scoped("good"), "name": "good"},
    ]
    api_session = Mock()
    api_session.get.side_effect = [
        _http_error(400),
        {"items": [{"principal": "jeremy@subimage.io", "permission": "MANAGE"}]},
    ]

    permissions, complete = (
        cartography.intel.databricks.permissions.get_secret_scope_acls(
            api_session, scopes
        )
    )

    assert complete is False
    assert len(permissions) == 1
    assert permissions[0]["principal"] == "jeremy@subimage.io"
    assert permissions[0]["object_id"] == scoped("good")


def test_get_secret_scope_acls_other_http_error_propagates():
    """A non-skippable status (e.g. 500) must abort so cleanup never runs on
    partial data."""
    scopes = [
        {"id": scoped("good"), "name": "good"},
    ]
    api_session = Mock()
    api_session.get.side_effect = _http_error(500)

    with pytest.raises(requests.HTTPError):
        cartography.intel.databricks.permissions.get_secret_scope_acls(
            api_session, scopes
        )
