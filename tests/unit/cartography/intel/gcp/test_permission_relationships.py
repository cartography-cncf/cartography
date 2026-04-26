from typing import Any
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


def _normalize_principals(principals: dict[str, Any]) -> dict[str, Any]:
    normalized: dict[str, Any] = {}
    for principal_email, bindings in principals.items():
        normalized[principal_email] = {}
        for binding_id, binding_data in bindings.items():
            normalized[principal_email][binding_id] = {
                "permissions": [
                    pattern.pattern
                    for pattern in binding_data["permissions"]["permissions"]
                ],
                "denied_permissions": [
                    pattern.pattern
                    for pattern in binding_data["permissions"]["denied_permissions"]
                ],
                "scope": binding_data["scope"].pattern,
            }
    return normalized


def test_get_principals_for_project_reads_policy_bindings_in_batches(monkeypatch):
    monkeypatch.setattr(
        permission_relationships,
        "GCP_POLICY_BINDING_READ_BATCH_SIZE",
        2,
    )
    rows_by_binding_id = {
        "binding-1": [
            {
                "principal_email": "alice@example.com",
                "binding_id": "binding-1",
                "binding_resource": "//cloudresourcemanager.googleapis.com/projects/project-abc",
                "role_permissions": ["storage.objects.get"],
            }
        ],
        "binding-2": [
            {
                "principal_email": "bob@example.com",
                "binding_id": "binding-2",
                "binding_resource": "//storage.googleapis.com/buckets/bucket-2",
                "role_permissions": ["storage.objects.get"],
            }
        ],
        "binding-3": [
            {
                "principal_email": "alice@example.com",
                "binding_id": "binding-3",
                "binding_resource": "//storage.googleapis.com/buckets/bucket-3",
                "role_permissions": ["storage.objects.create"],
            }
        ],
    }
    binding_batches = []

    def execute_read(tx_func, query, **kwargs):
        if tx_func is permission_relationships.read_list_of_values_tx:
            assert kwargs == {"ProjectId": TEST_PROJECT_ID}
            return ["binding-1", "binding-2", "binding-3"]

        assert tx_func is permission_relationships.read_list_of_dicts_tx
        assert kwargs["ProjectId"] == TEST_PROJECT_ID
        binding_batches.append(kwargs["BindingIds"])
        return [
            row
            for binding_id in kwargs["BindingIds"]
            for row in rows_by_binding_id[binding_id]
        ]

    neo4j_session = MagicMock()
    neo4j_session.execute_read.side_effect = execute_read

    principals = permission_relationships.get_principals_for_project(
        neo4j_session,
        TEST_PROJECT_ID,
    )

    assert binding_batches == [["binding-1", "binding-2"], ["binding-3"]]
    assert neo4j_session.execute_read.call_count == 3
    assert _normalize_principals(principals) == {
        "alice@example.com": {
            "binding-1": {
                "permissions": ["storage\\.objects\\.get"],
                "denied_permissions": [],
                "scope": "project/project-abc/.*",
            },
            "binding-3": {
                "permissions": ["storage\\.objects\\.create"],
                "denied_permissions": [],
                "scope": "project/project-abc/resource/bucket-3",
            },
        },
        "bob@example.com": {
            "binding-2": {
                "permissions": ["storage\\.objects\\.get"],
                "denied_permissions": [],
                "scope": "project/project-abc/resource/bucket-2",
            },
        },
    }


def test_get_principals_for_project_returns_empty_without_policy_bindings():
    neo4j_session = MagicMock()
    neo4j_session.execute_read.return_value = []

    principals = permission_relationships.get_principals_for_project(
        neo4j_session,
        TEST_PROJECT_ID,
    )

    assert principals == {}
    neo4j_session.execute_read.assert_called_once()


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
