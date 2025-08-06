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
                    "s3:listobject" "dynamodb:query",
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
                        "s3:listobject" "dynamodb:query",
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


def test_extract_properties_from_arn_deafult():
    schema = "{{arn}}"
    arn = "arn:aws:s3:::testbucket"

    result = permission_relationships.extract_properties_from_arn(arn, schema)
    expected = {"arn": "arn:aws:s3:::testbucket"}
    assert result == expected


def test_extract_properties_from_arn_custom_schema():
    schema = "arn:aws:ec2:{{region}}:*:instance/{{instanceid}}"
    arn = "arn:aws:ec2:us-east-1:*:instance/i-1234567890abcdef0"

    result = permission_relationships.extract_properties_from_arn(arn, schema)
    expected = {"region": "us-east-1", "instanceid": "i-1234567890abcdef0"}
    assert result == expected


def test_extract_properties_from_arn_s3path():
    schema = "{{arn}}/*"
    arn = "arn:aws:s3:::testbucket/*"

    result = permission_relationships.extract_properties_from_arn(arn, schema)
    expected = {"arn": "arn:aws:s3:::testbucket"}
    assert result == expected


def test_calculate_condition_clause_with_relations():
    ###
    # Test calculate_condition_clause with conditional target relations
    ###
    conditional_target_relations = ["HAS_INFORMATION", "BELONGS_TO"]

    result = permission_relationships.calculate_condition_clause(
        conditional_target_relations
    )

    expected = " WHERE ((resource)-[:HAS_INFORMATION]->() OR ()-[:HAS_INFORMATION]->(resource)) AND ((resource)-[:BELONGS_TO]->() OR ()-[:BELONGS_TO]->(resource))"
    assert result == expected


def test_calculate_condition_clause_with_single_relation():
    conditional_target_relations = ["HAS_INFORMATION"]

    result = permission_relationships.calculate_condition_clause(
        conditional_target_relations
    )

    expected = " WHERE ((resource)-[:HAS_INFORMATION]->() OR ()-[:HAS_INFORMATION]->(resource))"
    assert result == expected


def test_calculate_condition_clause_without_relations():
    conditional_target_relations = None

    result = permission_relationships.calculate_condition_clause(
        conditional_target_relations
    )

    assert result == ""


def test_calculate_condition_clause_with_empty_list():
    conditional_target_relations = []

    result = permission_relationships.calculate_condition_clause(
        conditional_target_relations
    )

    assert result == ""


def test_validate_resource_arn_schema_with_properties():
    schema = "arn:aws:ec2:{{region}}:{{accountid}}:instance/{{instanceid}}"

    result = permission_relationships.validate_resource_arn_schema(schema)

    assert result == schema


def test_validate_resource_arn_schema_without_properties():
    schema = "arn:aws:s3:::bucket"

    result = permission_relationships.validate_resource_arn_schema(schema)

    assert result == "{{arn}}"


def test_extract_properties_from_arn_with_invalid_match():
    ###
    # Test extract_properties_from_arn when regex match fails, to ensure regex pattern functions as intended.
    ###

    schema = "arn:aws:ec2:{{region}}:*:instance/{{instanceid}}"
    arn = "invalid-arn-format"  # Doesn't match the schema

    result = permission_relationships.extract_properties_from_arn(arn, schema)

    # Should return empty dict when no match
    assert result == {}
