from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from cartography.intel.gcp import permission_relationships

TEST_PROJECT_ID = "project-abc"
TEST_UPDATE_TAG = 123456789
COMMON_JOB_PARAMS = {
    "UPDATE_TAG": TEST_UPDATE_TAG,
    "ORG_RESOURCE_NAME": "organizations/1337",
    "PROJECT_ID": TEST_PROJECT_ID,
    "gcp_permission_relationships_file": "dummy_path",
}


def _build_policy_bindings(
    permissions: list[str],
    scope: str,
) -> dict[str, dict[str, object]]:
    return {
        "binding-1": {
            "permissions": permission_relationships.compile_permissions(
                {
                    "permissions": permissions,
                    "denied_permissions": [],
                }
            ),
            "scope": permission_relationships.compile_gcp_regex(scope),
        }
    }


def test_iter_permission_relationship_batches_preserves_matches():
    principals = {
        "alice@example.com": _build_policy_bindings(
            ["storage.objects.get"],
            "project/project-abc/resource/*",
        ),
        "bob@example.com": _build_policy_bindings(
            ["storage.objects.get"],
            "project/project-abc/resource/bucket-2",
        ),
    }
    resource_dict = {
        "bucket-1": "project/project-abc/resource/bucket-1",
        "bucket-2": "project/project-abc/resource/bucket-2",
        "bucket-3": "project/project-abc/resource/bucket-3",
    }
    permissions = ["storage.objects.get"]

    batches = list(
        permission_relationships.iter_permission_relationship_batches(
            principals,
            resource_dict,
            permissions,
            batch_size=2,
        )
    )
    flattened = [mapping for batch in batches for mapping in batch]

    assert all(len(batch) <= 2 for batch in batches)
    assert {tuple(sorted(mapping.items())) for mapping in flattened} == {
        (("principal_email", "alice@example.com"), ("resource_id", "bucket-1")),
        (("principal_email", "alice@example.com"), ("resource_id", "bucket-2")),
        (("principal_email", "alice@example.com"), ("resource_id", "bucket-3")),
        (("principal_email", "bob@example.com"), ("resource_id", "bucket-2")),
    }


def test_sync_loads_permission_relationships_in_multiple_batches(monkeypatch):
    principals = {
        "alice@example.com": _build_policy_bindings(
            ["storage.objects.get"],
            "project/project-abc/resource/*",
        ),
    }
    resource_dict = {
        "bucket-1": "project/project-abc/resource/bucket-1",
        "bucket-2": "project/project-abc/resource/bucket-2",
        "bucket-3": "project/project-abc/resource/bucket-3",
    }
    relationship_mapping = [
        {
            "permissions": ["storage.objects.get"],
            "relationship_name": "CAN_READ",
            "target_label": "GCPBucket",
        }
    ]
    neo4j_session = MagicMock()

    monkeypatch.setattr(
        permission_relationships,
        "GCP_PERMISSION_RELATIONSHIP_BATCH_SIZE",
        2,
    )

    with (
        patch.object(
            permission_relationships,
            "get_principals_for_project",
            return_value=principals,
        ),
        patch.object(
            permission_relationships,
            "parse_permission_relationships_file",
            return_value=relationship_mapping,
        ),
        patch.object(
            permission_relationships,
            "get_resource_ids",
            return_value=resource_dict,
        ),
        patch.object(
            permission_relationships,
            "load_principal_mappings",
        ) as mock_load_principal_mappings,
        patch.object(
            permission_relationships,
            "cleanup_rpr",
        ) as mock_cleanup_rpr,
    ):
        permission_relationships.sync(
            neo4j_session,
            TEST_PROJECT_ID,
            TEST_UPDATE_TAG,
            COMMON_JOB_PARAMS,
        )

    assert mock_load_principal_mappings.call_count == 2
    assert [
        len(call.args[1]) for call in mock_load_principal_mappings.call_args_list
    ] == [
        2,
        1,
    ]
    mock_cleanup_rpr.assert_called_once()


def test_sync_skips_cleanup_when_batch_load_fails(monkeypatch):
    principals = {
        "alice@example.com": _build_policy_bindings(
            ["storage.objects.get"],
            "project/project-abc/resource/*",
        ),
    }
    resource_dict = {
        "bucket-1": "project/project-abc/resource/bucket-1",
        "bucket-2": "project/project-abc/resource/bucket-2",
    }
    relationship_mapping = [
        {
            "permissions": ["storage.objects.get"],
            "relationship_name": "CAN_READ",
            "target_label": "GCPBucket",
        }
    ]
    neo4j_session = MagicMock()

    monkeypatch.setattr(
        permission_relationships,
        "GCP_PERMISSION_RELATIONSHIP_BATCH_SIZE",
        2,
    )

    with (
        patch.object(
            permission_relationships,
            "get_principals_for_project",
            return_value=principals,
        ),
        patch.object(
            permission_relationships,
            "parse_permission_relationships_file",
            return_value=relationship_mapping,
        ),
        patch.object(
            permission_relationships,
            "get_resource_ids",
            return_value=resource_dict,
        ),
        patch.object(
            permission_relationships,
            "load_principal_mappings",
            side_effect=RuntimeError("boom"),
        ),
        patch.object(
            permission_relationships,
            "cleanup_rpr",
        ) as mock_cleanup_rpr,
    ):
        with pytest.raises(RuntimeError, match="boom"):
            permission_relationships.sync(
                neo4j_session,
                TEST_PROJECT_ID,
                TEST_UPDATE_TAG,
                COMMON_JOB_PARAMS,
            )

    mock_cleanup_rpr.assert_not_called()
