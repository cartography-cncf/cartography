import json

import pytest

from cartography.intel.aws import permission_relationships

GET_OBJECT_LOWERCASE_RESOURCE_WILDCARD = [
    {
        "action": [
            "s3:Get*",
        ],
        "resource": [
            "arn:aws:s3:::test*",
        ],
        "effect": "Allow",
    },
]


def test_admin_statements():
    statement = [
        {
            "action": [
                "*",
            ],
            "resource": [
                "*",
            ],
            "effect": "Allow",
        },
    ]
    assert (True, False) == permission_relationships.evaluate_policy_for_permissions(
        statement,
        ["S3:GetObject"],
        "arn:aws:s3:::testbucket",
    )


def test_not_action_statement():
    statement = [
        {
            "action": [
                "*",
            ],
            "notaction": [
                "S3:GetObject",
            ],
            "resource": [
                "*",
            ],
            "effect": "Allow",
        },
    ]
    assert (False, False) == permission_relationships.evaluate_policy_for_permissions(
        statement,
        ["S3:GetObject"],
        "arn:aws:s3:::testbucket",
    )


def test_deny_statement():
    statement = [
        {
            "action": [
                "*",
            ],
            "resource": [
                "*",
            ],
            "effect": "Allow",
        },
        {
            "action": [
                "S3:GetObject",
            ],
            "resource": [
                "*",
            ],
            "effect": "Deny",
        },
    ]
    assert (False, True) == permission_relationships.evaluate_policy_for_permissions(
        statement,
        ["S3:GetObject"],
        "arn:aws:s3:::testbucket",
    )


def test_single_permission():
    statement = [
        {
            "action": [
                "S3:GetObject",
            ],
            "resource": [
                "*",
            ],
            "effect": "Allow",
        },
    ]
    assert (True, False) == permission_relationships.evaluate_policy_for_permissions(
        statement,
        ["S3:GetObject"],
        "arn:aws:s3:::testbucket",
    )


def test_single_non_matching_permission():
    statement = [
        {
            "action": [
                "S3:GetObject",
            ],
            "resource": [
                "*",
            ],
            "effect": "Allow",
        },
    ]
    assert (False, False) == permission_relationships.evaluate_policy_for_permissions(
        statement,
        ["S3:PutObject"],
        "arn:aws:s3:::testbucket",
    )


def test_multiple_permission():
    statement = [
        {
            "action": [
                "S3:GetObject",
            ],
            "resource": [
                "*",
            ],
            "effect": "Allow",
        },
    ]
    assert (True, False) == permission_relationships.evaluate_policy_for_permissions(
        statement,
        ["S3:GetObject", "S3:PutObject", "S3:ListBuckets"],
        "arn:aws:s3:::testbucket",
    )


def test_multiple_non_matching_permission():
    statement = [
        {
            "action": [
                "S3:GetObject",
            ],
            "resource": [
                "*",
            ],
            "effect": "Allow",
        },
    ]
    assert (False, False) == permission_relationships.evaluate_policy_for_permissions(
        statement,
        ["S3:PutObject", "S3:ListBuckets"],
        "arn:aws:s3:::testbucket",
    )


def test_single_permission_lower_case():
    statement = [
        {
            "action": [
                "s3:Get*",
            ],
            "resource": [
                "*",
            ],
            "effect": "Allow",
        },
    ]
    assert (True, False) == permission_relationships.evaluate_policy_for_permissions(
        statement,
        ["S3:GetObject"],
        "arn:aws:s3:::testbucket",
    )


def test_single_permission_resource_allow():
    statement = [
        {
            "action": [
                "s3:Get*",
            ],
            "resource": [
                "arn:aws:s3:::test*",
            ],
            "effect": "Allow",
        },
    ]
    assert (True, False) == permission_relationships.evaluate_policy_for_permissions(
        statement,
        ["S3:GetObject"],
        "arn:aws:s3:::testbucket",
    )


def test_single_permission_resource_non_match():
    statement = [
        {
            "action": [
                "s3:Get*",
            ],
            "resource": [
                "arn:aws:s3:::nottest",
            ],
            "effect": "Allow",
        },
    ]
    assert (False, False) == permission_relationships.evaluate_policy_for_permissions(
        statement,
        ["S3:GetObject"],
        "arn:aws:s3:::testbucket",
    )


def test_object_level_resource_matches_bucket():
    # An object-level grant (arn:aws:s3:::my-bucket/*) should draw an edge to the
    # bucket node (arn:aws:s3:::my-bucket). See issue #1639.
    statement = [
        {
            "action": [
                "s3:GetObject",
            ],
            "resource": [
                "arn:aws:s3:::my-bucket/*",
            ],
            "effect": "Allow",
        },
    ]
    assert (True, False) == permission_relationships.evaluate_policy_for_permissions(
        statement,
        ["S3:GetObject"],
        "arn:aws:s3:::my-bucket",
    )


def test_object_level_resource_prefix_grant_matches_bucket():
    # An object-level grant scoped to a key prefix (arn:aws:s3:::my-bucket/logs/*)
    # should still draw an edge to the bucket node. See issue #1639.
    statement = [
        {
            "action": [
                "s3:GetObject",
            ],
            "resource": [
                "arn:aws:s3:::my-bucket/logs/*",
            ],
            "effect": "Allow",
        },
    ]
    assert (True, False) == permission_relationships.evaluate_policy_for_permissions(
        statement,
        ["S3:GetObject"],
        "arn:aws:s3:::my-bucket",
    )


def test_object_level_resource_does_not_match_other_bucket():
    # The trailing-slash match must not leak across buckets with a shared prefix.
    statement = [
        {
            "action": [
                "s3:GetObject",
            ],
            "resource": [
                "arn:aws:s3:::my-bucket/*",
            ],
            "effect": "Allow",
        },
    ]
    assert (False, False) == permission_relationships.evaluate_policy_for_permissions(
        statement,
        ["S3:GetObject"],
        "arn:aws:s3:::my-bucket-other",
    )


def test_object_level_match_scoped_to_s3():
    # The trailing-slash match must not apply to non-S3 resources: a grant on
    # ".../PassableRole/*" targets a different role path, not an object under
    # the role, so it must NOT match the parent role node.
    statement = [
        {
            "action": [
                "iam:PassRole",
            ],
            "resource": [
                "arn:aws:iam::000000000000:role/PassableRole/*",
            ],
            "effect": "Allow",
        },
    ]
    assert (False, False) == permission_relationships.evaluate_policy_for_permissions(
        statement,
        ["iam:PassRole"],
        "arn:aws:iam::000000000000:role/PassableRole",
    )


def test_object_level_notresource_does_not_exclude_bucket():
    # A notresource scoped to objects (arn:aws:s3:::my-bucket/*) excludes the
    # bucket *objects*, not the bucket ARN itself, so bucket-level permissions
    # on the bucket node are still allowed by AWS and the edge must remain.
    statements = [
        {
            "action": [
                "s3:Get*",
            ],
            "resource": ["*"],
            "notresource": [
                "arn:aws:s3:::my-bucket/*",
            ],
            "effect": "Allow",
        },
    ]
    assert (True, False) == permission_relationships.evaluate_policy_for_permissions(
        statements,
        ["S3:GetObject"],
        "arn:aws:s3:::my-bucket",
    )


def test_non_matching_notresource():
    statements = [
        {
            "action": [
                "s3:Get*",
            ],
            "resource": ["*"],
            "notresource": [
                "arn:aws:s3:::nottest",
            ],
            "effect": "Allow",
        },
    ]
    assert (True, False) == permission_relationships.evaluate_policy_for_permissions(
        statements,
        ["S3:GetObject"],
        "arn:aws:s3:::testbucket",
    )


def test_no_action_statement():
    statements = [
        {
            "notaction": [
                "dynamodb:Query",
            ],
            "resource": [
                "*",
            ],
            "effect": "Allow",
        },
    ]
    assert (True, False) == permission_relationships.evaluate_policy_for_permissions(
        statements,
        ["S3:GetObject"],
        "arn:aws:s3:::testbucket",
    )


def test_notaction_deny_without_allow():
    statements = [
        {
            "notaction": [
                "s3:*",
            ],
            "resource": [
                "*",
            ],
            "effect": "Allow",
        },
    ]
    assert (False, False) == permission_relationships.evaluate_policy_for_permissions(
        statements,
        ["S3:GetObject"],
        "arn:aws:s3:::testbucket",
    )


def test_notaction_malformed():
    statements = [
        {
            "notaction": [
                "s3.*",
            ],
            "resource": [
                "*",
            ],
            "effect": "Allow",
        },
    ]
    assert (True, False) == permission_relationships.evaluate_policy_for_permissions(
        statements,
        ["S3:GetObject"],
        "arn:aws:s3:::testbucket",
    )


def test_resource_substring():
    statements = [
        {
            "action": [
                "s3.*",
            ],
            "resource": [
                "arn:aws:s3:::test",
            ],
            "effect": "Allow",
        },
    ]
    assert (False, False) == permission_relationships.evaluate_policy_for_permissions(
        statements,
        ["S3:GetObject"],
        "arn:aws:s3:::testbucket",
    )


def test_full_policy_explicit_deny():
    policies = {
        "fakeallow": [
            {
                "action": [
                    "s3:*",
                ],
                "resource": [
                    "*",
                ],
                "effect": "Allow",
            },
        ],
        "fakedeny": [
            {
                "action": [
                    "s3:*",
                ],
                "resource": [
                    "arn:aws:s3:::testbucket",
                ],
                "effect": "Deny",
            },
        ],
    }
    assert not permission_relationships.principal_allowed_on_resource(
        policies,
        "arn:aws:s3:::testbucket",
        ["S3:GetObject"],
    )


def test_full_policy_no_explicit_allow():
    policies = {
        "ListAllow": [
            {
                "action": [
                    "s3:List*",
                ],
                "resource": [
                    "*",
                ],
                "effect": "Allow",
            },
        ],
        "PutAllow": [
            {
                "action": [
                    "s3:Put*",
                ],
                "resource": [
                    "arn:aws:s3:::testbucket",
                ],
                "effect": "Allow",
            },
        ],
    }
    assert not permission_relationships.principal_allowed_on_resource(
        policies,
        "arn:aws:s3:::testbucket",
        ["S3:GetObject"],
    )


def test_full_policy_explicit_allow():
    policies = {
        "ListAllow": [
            {
                "action": [
                    "s3:listobjectdynamodb:query",
                ],
                "resource": [
                    "*",
                ],
                "effect": "Allow",
            },
        ],
        "explicitallow": [
            {
                "action": [
                    "s3:getobject",
                ],
                "resource": [
                    "arn:aws:s3:::testbucket",
                ],
                "effect": "Allow",
            },
        ],
    }
    assert permission_relationships.principal_allowed_on_resource(
        policies,
        "arn:aws:s3:::testbucket",
        ["S3:GetObject"],
    )


def test_full_multiple_principal():
    principals = {
        "test_principals1": {
            "ListAllow": [
                {
                    "action": [
                        "s3:listobjectdynamodb:query",
                    ],
                    "resource": [
                        "*",
                    ],
                    "effect": "Allow",
                },
            ],
            "explicitallow": [
                {
                    "action": [
                        "s3:getobject",
                    ],
                    "resource": [
                        "arn:aws:s3:::testbucket",
                    ],
                    "effect": "Allow",
                },
            ],
        },
        "test_principal2": {
            "ListAllow": [
                {
                    "action": [
                        "s3:List*",
                    ],
                    "resource": [
                        "*",
                    ],
                    "effect": "Allow",
                },
            ],
            "PutAllow": [
                {
                    "action": [
                        "s3:Put*",
                    ],
                    "resource": [
                        "arn:aws:s3:::testbucket",
                    ],
                    "effect": "Allow",
                },
            ],
        },
    }
    assert 1 == len(
        permission_relationships.calculate_permission_relationships(
            principals,
            ["arn:aws:s3:::testbucket"],
            ["S3:GetObject"],
        ),
    )


def test_single_comma():
    statements = [
        {
            "action": [
                "s3:?et*",
            ],
            "resource": ["arn:aws:s3:::testbucke?"],
            "effect": "Allow",
        },
    ]
    assert (True, False) == permission_relationships.evaluate_policy_for_permissions(
        statements,
        ["S3:GetObject"],
        "arn:aws:s3:::testbucket",
    )


def test_multiple_comma():
    statements = [
        {
            "action": [
                "s3:?et*",
            ],
            "resource": ["arn:aws:s3:::????bucket"],
            "effect": "Allow",
        },
    ]
    assert (True, False) == permission_relationships.evaluate_policy_for_permissions(
        statements,
        ["S3:GetObject"],
        "arn:aws:s3:::testbucket",
    )


def test_evaluate_clause_with_none_match():
    with pytest.raises(ValueError, match="match must not be None"):
        permission_relationships.evaluate_clause("*", None)


# --- Target preconditions on permission relationships (issue #1643) ---


def test_build_target_precondition_clause_empty():
    assert permission_relationships.build_target_precondition_clause(None) == ""
    assert permission_relationships.build_target_precondition_clause({}) == ""


def test_build_target_precondition_clause_outgoing():
    clause = permission_relationships.build_target_precondition_clause(
        {
            "related_label": "AWSSSMInstanceInformation",
            "relationship": "HAS_INFORMATION",
            "direction": "outgoing",
        },
    )
    assert (
        clause
        == "AND EXISTS { MATCH (resource)-[:HAS_INFORMATION]->(:AWSSSMInstanceInformation) }"
    )


def test_build_target_precondition_clause_defaults_to_outgoing():
    clause = permission_relationships.build_target_precondition_clause(
        {
            "related_label": "AWSSSMInstanceInformation",
            "relationship": "HAS_INFORMATION",
        },
    )
    assert "(resource)-[:HAS_INFORMATION]->(:AWSSSMInstanceInformation)" in clause


def test_build_target_precondition_clause_incoming():
    clause = permission_relationships.build_target_precondition_clause(
        {
            "related_label": "SomeNode",
            "relationship": "POINTS_TO",
            "direction": "incoming",
        },
    )
    assert clause == "AND EXISTS { MATCH (resource)<-[:POINTS_TO]-(:SomeNode) }"


def test_build_target_precondition_clause_rejects_invalid_direction():
    with pytest.raises(ValueError, match="direction must be"):
        permission_relationships.build_target_precondition_clause(
            {
                "related_label": "AWSSSMInstanceInformation",
                "relationship": "HAS_INFORMATION",
                "direction": "sideways",
            },
        )


def test_is_valid_rpr_accepts_valid_precondition():
    assert permission_relationships.is_valid_rpr(
        {
            "permissions": ["ssm:StartSession"],
            "relationship_name": "CAN_START_SESSION",
            "target_label": "AWSEC2Instance",
            "target_precondition": {
                "related_label": "AWSSSMInstanceInformation",
                "relationship": "HAS_INFORMATION",
            },
        },
    )


def test_is_valid_rpr_rejects_malformed_precondition():
    assert not permission_relationships.is_valid_rpr(
        {
            "permissions": ["ssm:StartSession"],
            "relationship_name": "CAN_START_SESSION",
            "target_label": "AWSEC2Instance",
            "target_precondition": {"related_label": "AWSSSMInstanceInformation"},
        },
    )
    assert not permission_relationships.is_valid_rpr(
        {
            "permissions": ["ssm:StartSession"],
            "relationship_name": "CAN_START_SESSION",
            "target_label": "AWSEC2Instance",
            "target_precondition": "not-a-dict",
        },
    )


def test_permission_file_load():
    mapping = permission_relationships.parse_permission_relationships_file(
        "cartography/data/permission_relationships.yaml",
    )
    assert mapping


def test_permission_file_load_exception():
    mapping = permission_relationships.parse_permission_relationships_file(
        "notarealfile",
    )
    assert not mapping


def test_permissions_list():
    ###
    # Tests that the an exception is thrown if the permissions is not a list
    ###
    try:
        assert not permission_relationships.principal_allowed_on_resource(
            GET_OBJECT_LOWERCASE_RESOURCE_WILDCARD,
            "arn:aws:s3:::testbucket",
            "S3:GetObject",
        )
        assert False
    except ValueError:
        assert True


# --- IAM Condition modeling (issue #2250) ---


def test_extract_condition_context_keys_from_json_string():
    blob = json.dumps(
        [
            {"IpAddress": {"aws:SourceIp": "10.0.0.0/8"}},
            {"Bool": {"aws:MultiFactorAuthPresent": "true"}},
        ],
    )
    assert permission_relationships.extract_condition_context_keys(blob) == [
        "aws:MultiFactorAuthPresent",
        "aws:SourceIp",
    ]


def test_extract_condition_context_keys_handles_empty_and_malformed():
    assert permission_relationships.extract_condition_context_keys(None) == []
    assert permission_relationships.extract_condition_context_keys("") == []
    assert permission_relationships.extract_condition_context_keys("not-json") == []


def test_collect_edge_conditions_unconditional():
    policies = {
        "AllowS3": [
            {
                "action": ["s3:GetObject"],
                "resource": ["*"],
                "effect": "Allow",
            },
        ],
    }
    result = permission_relationships.collect_edge_conditions(
        policies,
        "arn:aws:s3:::testbucket",
        ["S3:GetObject"],
    )
    assert result == {"has_condition": False, "condition_keys": [], "conditions": None}


def test_collect_edge_conditions_conditional():
    condition = json.dumps([{"IpAddress": {"aws:SourceIp": "10.0.0.0/8"}}])
    policies = {
        "AllowS3FromVpn": [
            {
                "action": ["s3:GetObject"],
                "resource": ["*"],
                "effect": "Allow",
                "condition": condition,
            },
        ],
    }
    result = permission_relationships.collect_edge_conditions(
        policies,
        "arn:aws:s3:::testbucket",
        ["S3:GetObject"],
    )
    assert result["has_condition"] is True
    assert result["condition_keys"] == ["aws:SourceIp"]
    assert json.loads(result["conditions"]) == json.loads(condition)


def test_collect_edge_conditions_malformed_condition_fails_safe():
    # A statement that carries a Condition but whose blob can't be parsed must NOT be
    # downgraded to an unconditional grant; the edge stays flagged conditional.
    policies = {
        "MalformedCondition": [
            {
                "action": ["s3:GetObject"],
                "resource": ["*"],
                "effect": "Allow",
                "condition": "not-valid-json",
            },
        ],
    }
    result = permission_relationships.collect_edge_conditions(
        policies,
        "arn:aws:s3:::testbucket",
        ["S3:GetObject"],
    )
    assert result["has_condition"] is True
    assert result["conditions"] is not None


def test_collect_edge_conditions_unconditional_path_wins():
    # If one matching Allow is conditional but another grants the same access
    # unconditionally, the edge is effectively unconditional.
    condition = json.dumps([{"IpAddress": {"aws:SourceIp": "10.0.0.0/8"}}])
    policies = {
        "Conditional": [
            {
                "action": ["s3:GetObject"],
                "resource": ["*"],
                "effect": "Allow",
                "condition": condition,
            },
        ],
        "Unconditional": [
            {
                "action": ["s3:*"],
                "resource": ["*"],
                "effect": "Allow",
            },
        ],
    }
    result = permission_relationships.collect_edge_conditions(
        policies,
        "arn:aws:s3:::testbucket",
        ["S3:GetObject"],
    )
    assert result["has_condition"] is False


def test_calculate_permission_relationships_flags_conditional_edge():
    condition = json.dumps([{"Bool": {"aws:MultiFactorAuthPresent": "true"}}])
    principals = {
        "arn:aws:iam::000000000000:role/Conditional": {
            "MFAOnly": [
                {
                    "action": ["s3:GetObject"],
                    "resource": ["*"],
                    "effect": "Allow",
                    "condition": condition,
                },
            ],
        },
        "arn:aws:iam::000000000000:role/Open": {
            "Open": [
                {
                    "action": ["s3:GetObject"],
                    "resource": ["*"],
                    "effect": "Allow",
                },
            ],
        },
    }
    mappings = permission_relationships.calculate_permission_relationships(
        principals,
        ["arn:aws:s3:::testbucket"],
        ["S3:GetObject"],
    )
    by_principal = {m["principal_arn"]: m for m in mappings}
    assert (
        by_principal["arn:aws:iam::000000000000:role/Conditional"]["has_condition"]
        is True
    )
    assert by_principal["arn:aws:iam::000000000000:role/Conditional"][
        "condition_keys"
    ] == ["aws:MultiFactorAuthPresent"]
    assert by_principal["arn:aws:iam::000000000000:role/Open"]["has_condition"] is False
