import logging
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


def test_build_principals_from_policy_bindings_uses_in_memory_role_permissions():
    policy_bindings = [
        {
            "id": "binding-1",
            "role": "roles/storage.objectViewer",
            "resource": "//cloudresourcemanager.googleapis.com/projects/project-abc",
            "members": ["alice@example.com"],
            "has_condition": False,
        },
        {
            "id": "binding-2",
            "role": "roles/storage.objectViewer",
            "resource": "//storage.googleapis.com/buckets/bucket-2",
            "members": ["bob@example.com"],
            "has_condition": False,
        },
        {
            "id": "binding-3",
            "role": "roles/storage.objectCreator",
            "resource": "//storage.googleapis.com/buckets/bucket-3",
            "members": ["alice@example.com"],
            "has_condition": False,
        },
    ]
    role_permissions_by_name = {
        "roles/storage.objectViewer": ["storage.objects.get"],
        "roles/storage.objectCreator": ["storage.objects.create"],
    }

    principals = permission_relationships.build_principals_from_policy_bindings(
        policy_bindings,
        role_permissions_by_name,
        TEST_PROJECT_ID,
    )

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
                "scope": "project/project-abc/resource/buckets/bucket-3",
            },
        },
        "bob@example.com": {
            "binding-2": {
                "permissions": ["storage\\.objects\\.get"],
                "denied_permissions": [],
                "scope": "project/project-abc/resource/buckets/bucket-2",
            },
        },
    }


def test_build_principals_from_policy_bindings_logs_context_diagnostics(caplog):
    policy_bindings = [
        {
            "id": "binding-1",
            "role": "roles/storage.objectViewer",
            "resource": "//cloudresourcemanager.googleapis.com/projects/project-abc",
            "members": ["alice@example.com"],
            "has_condition": False,
        },
        {
            "id": "binding-2",
            "role": "roles/storage.objectViewer",
            "resource": "//storage.googleapis.com/buckets/bucket-2",
            "members": ["bob@example.com"],
            "has_condition": False,
        },
        {
            "id": "binding-3",
            "role": "roles/storage.admin",
            "resource": "//storage.googleapis.com/buckets/bucket-3",
            "members": ["alice@example.com"],
            "has_condition": True,
        },
        {
            "id": "binding-4",
            "role": "roles/missing",
            "resource": "//storage.googleapis.com/buckets/bucket-4",
            "members": ["carol@example.com"],
            "has_condition": False,
        },
    ]
    with caplog.at_level(logging.DEBUG):
        principals = permission_relationships.build_principals_from_policy_bindings(
            policy_bindings,
            {"roles/storage.objectViewer": ["storage.objects.get"]},
            TEST_PROJECT_ID,
        )

    assert _normalize_principals(principals) == {
        "alice@example.com": {
            "binding-1": {
                "permissions": ["storage\\.objects\\.get"],
                "denied_permissions": [],
                "scope": "project/project-abc/.*",
            },
        },
        "bob@example.com": {
            "binding-2": {
                "permissions": ["storage\\.objects\\.get"],
                "denied_permissions": [],
                "scope": "project/project-abc/resource/buckets/bucket-2",
            },
        },
    }
    assert any(
        "usable_bindings=2" in record.message
        and "member_assignments=2" in record.message
        and "principals=2" in record.message
        and "skipped_conditional=1" in record.message
        and "skipped_missing_roles=1" in record.message
        for record in caplog.records
        if record.levelno == logging.INFO
    )


def test_build_principals_from_policy_bindings_returns_empty_without_policy_bindings():
    principals = permission_relationships.build_principals_from_policy_bindings(
        [],
        {},
        TEST_PROJECT_ID,
    )

    assert principals == {}


def test_build_principals_from_policy_bindings_reuses_compiled_assignments_per_binding():
    policy_bindings = [
        {
            "id": "binding-1",
            "role": "roles/storage.objectViewer",
            "resource": "//storage.googleapis.com/buckets/shared-bucket",
            "members": ["alice@example.com", "bob@example.com"],
            "has_condition": False,
        },
    ]
    compiled_permissions = {"permissions": ["compiled"], "denied_permissions": []}
    compiled_scope = MagicMock()

    with (
        patch.object(
            permission_relationships,
            "compile_permissions_from_role",
            return_value=compiled_permissions,
        ) as mock_compile_permissions,
        patch.object(
            permission_relationships,
            "resolve_gcp_scope",
            return_value="project/project-abc/resource/buckets/shared-bucket",
        ),
        patch.object(
            permission_relationships,
            "compile_gcp_regex",
            return_value=compiled_scope,
        ) as mock_compile_scope,
    ):
        principals = permission_relationships.build_principals_from_policy_bindings(
            policy_bindings,
            {"roles/storage.objectViewer": ["storage.objects.get"]},
            TEST_PROJECT_ID,
        )

    mock_compile_permissions.assert_called_once_with(["storage.objects.get"])
    mock_compile_scope.assert_called_once_with(
        "project/project-abc/resource/buckets/shared-bucket"
    )
    assert (
        principals["alice@example.com"]["binding-1"]["permissions"]
        is compiled_permissions
    )
    assert (
        principals["bob@example.com"]["binding-1"]["permissions"]
        is compiled_permissions
    )
    assert principals["alice@example.com"]["binding-1"]["scope"] is compiled_scope
    assert principals["bob@example.com"]["binding-1"]["scope"] is compiled_scope


@pytest.mark.parametrize(
    "target_label,resource_id,expected",
    [
        # Default: id is already the path used in IAM scope strings.
        (
            "GCPCryptoKey",
            "projects/p/locations/us/keyRings/kr/cryptoKeys/k",
            "projects/p/locations/us/keyRings/kr/cryptoKeys/k",
        ),
        # GCS buckets: bare name needs a "buckets/" prefix.
        ("GCPBucket", "my-bucket", "buckets/my-bucket"),
        # BigQuery dataset: legacy "project:dataset" -> path form.
        (
            "GCPBigQueryDataset",
            "my-project:analytics",
            "projects/my-project/datasets/analytics",
        ),
        # BigQuery table: legacy "project:dataset.table" -> path form.
        (
            "GCPBigQueryTable",
            "my-project:analytics.events",
            "projects/my-project/datasets/analytics/tables/events",
        ),
        # BigQuery dataset with no ":" (defensive: leave as-is).
        ("GCPBigQueryDataset", "already-fine", "already-fine"),
    ],
)
def test_canonical_resource_path(target_label, resource_id, expected):
    assert (
        permission_relationships._canonical_resource_path(target_label, resource_id)
        == expected
    )


def test_iter_permission_relationship_batches_preserves_matches():
    principals = {
        "alice@example.com": _build_policy_bindings(
            ["storage.objects.get"],
            "project/project-abc/resource/*",
        ),
        "bob@example.com": _build_policy_bindings(
            ["storage.objects.get"],
            "project/project-abc/resource/buckets/bucket-2",
        ),
    }
    resource_dict = {
        "bucket-1": "project/project-abc/resource/buckets/bucket-1",
        "bucket-2": "project/project-abc/resource/buckets/bucket-2",
        "bucket-3": "project/project-abc/resource/buckets/bucket-3",
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
        "bucket-1": "project/project-abc/resource/buckets/bucket-1",
        "bucket-2": "project/project-abc/resource/buckets/bucket-2",
        "bucket-3": "project/project-abc/resource/buckets/bucket-3",
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
            principals,
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
        "bucket-1": "project/project-abc/resource/buckets/bucket-1",
        "bucket-2": "project/project-abc/resource/buckets/bucket-2",
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
                principals,
            )

    mock_cleanup_rpr.assert_not_called()
