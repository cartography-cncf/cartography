import datetime
import json

import pytest

import tests.data.aws.iam
from cartography.intel.aws.iam import transform_role_trust_policies

TEST_ACCOUNT_ID = "000000000000"
GITHUB_OIDC_PROVIDER_ARN = tests.data.aws.iam.GITHUB_OIDC_PROVIDER_ARN


def _trusts_by_role(transformed):
    return {
        (t["source_role_arn"], t["target_principal_arn"]): t
        for t in transformed.trust_relationships
    }


def test_oidc_trusts_differing_only_in_sub_scoping_are_distinguishable():
    """Two roles identical apart from their sub condition must not collapse to the same edge."""
    transformed = transform_role_trust_policies(
        tests.data.aws.iam.LIST_ROLES_GITHUB_OIDC["Roles"], TEST_ACCOUNT_ID
    )
    trusts = _trusts_by_role(transformed)

    pinned = trusts[
        (
            "arn:aws:iam::000000000000:role/gha-pinned",
            GITHUB_OIDC_PROVIDER_ARN,
        )
    ]
    org_wide = trusts[
        (
            "arn:aws:iam::000000000000:role/gha-org-wide",
            GITHUB_OIDC_PROVIDER_ARN,
        )
    ]

    # Both are conditional and reference the same context keys...
    assert pinned["has_condition"] is True
    assert org_wide["has_condition"] is True
    assert (
        pinned["condition_keys"]
        == org_wide["condition_keys"]
        == [
            "token.actions.githubusercontent.com:aud",
            "token.actions.githubusercontent.com:sub",
        ]
    )

    # ...but the retained condition blobs tell them apart, which is the point.
    assert pinned["conditions"] != org_wide["conditions"]
    assert json.loads(pinned["conditions"]) == [
        {
            "StringEquals": {
                "token.actions.githubusercontent.com:aud": "sts.amazonaws.com",
                "token.actions.githubusercontent.com:sub": "repo:octo-org/octo-repo:ref:refs/heads/main",
            }
        }
    ]
    assert json.loads(org_wide["conditions"]) == [
        {
            "StringLike": {
                "token.actions.githubusercontent.com:aud": "sts.amazonaws.com",
                "token.actions.githubusercontent.com:sub": "repo:octo-org/*",
            }
        }
    ]


def test_unconditional_statement_wins_over_conditional_one():
    """A role trusting one principal from both a gated and an ungated statement is unconditional."""
    transformed = transform_role_trust_policies(
        tests.data.aws.iam.LIST_ROLES_GITHUB_OIDC["Roles"], TEST_ACCOUNT_ID
    )
    mixed = _trusts_by_role(transformed)[
        (
            "arn:aws:iam::000000000000:role/gha-mixed",
            GITHUB_OIDC_PROVIDER_ARN,
        )
    ]

    assert mixed["has_condition"] is False
    assert mixed["condition_keys"] == []
    assert mixed["conditions"] is None


def test_one_row_per_role_principal_pair():
    """A principal trusted by several statements of one role yields a single aggregated row."""
    transformed = transform_role_trust_policies(
        tests.data.aws.iam.LIST_ROLES_GITHUB_OIDC["Roles"], TEST_ACCOUNT_ID
    )

    pairs = [
        (t["source_role_arn"], t["target_principal_arn"])
        for t in transformed.trust_relationships
    ]
    assert len(pairs) == len(set(pairs))
    # gha-mixed trusts the provider from two statements but contributes one row.
    assert (
        sum(
            1
            for role_arn, _ in pairs
            if role_arn == "arn:aws:iam::000000000000:role/gha-mixed"
        )
        == 1
    )


def test_conditions_are_aggregated_across_statements():
    """Two differently gated statements for one principal keep both blobs and the key union."""
    role = {
        "Path": "/",
        "RoleName": "two-gates",
        "RoleId": "AROA00000000000000013",
        "Arn": "arn:aws:iam::000000000000:role/two-gates",
        "CreateDate": datetime.datetime(2026, 1, 1, 0, 0, 1),
        "AssumeRolePolicyDocument": {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Action": "sts:AssumeRoleWithWebIdentity",
                    "Effect": "Allow",
                    "Principal": {"Federated": GITHUB_OIDC_PROVIDER_ARN},
                    "Condition": {
                        "StringEquals": {
                            "token.actions.githubusercontent.com:sub": "repo:octo-org/repo-a:ref:refs/heads/main",
                        },
                    },
                },
                {
                    "Action": "sts:AssumeRoleWithWebIdentity",
                    "Effect": "Allow",
                    "Principal": {"Federated": GITHUB_OIDC_PROVIDER_ARN},
                    "Condition": {
                        "StringEquals": {
                            "token.actions.githubusercontent.com:aud": "sts.amazonaws.com",
                        },
                    },
                },
            ],
        },
    }

    transformed = transform_role_trust_policies([role], TEST_ACCOUNT_ID)
    (trust,) = transformed.trust_relationships

    assert trust["has_condition"] is True
    assert trust["condition_keys"] == [
        "token.actions.githubusercontent.com:aud",
        "token.actions.githubusercontent.com:sub",
    ]
    assert len(json.loads(trust["conditions"])) == 2


def test_saml_trust_condition_is_retained():
    """The SAML:aud condition already present in the shared fixture reaches the edge."""
    transformed = transform_role_trust_policies(
        tests.data.aws.iam.LIST_ROLES["Roles"], TEST_ACCOUNT_ID
    )
    saml = _trusts_by_role(transformed)[
        (
            "arn:aws:iam::000000000000:role/example-role-3",
            "arn:aws:iam::000000000000:saml-provider/ADFS",
        )
    ]

    assert saml["has_condition"] is True
    assert saml["condition_keys"] == ["SAML:aud"]


def test_unconditional_trusts_are_not_flagged():
    """Trusts with no Condition keep has_condition false and carry no blob."""
    transformed = transform_role_trust_policies(
        tests.data.aws.iam.LIST_ROLES["Roles"], TEST_ACCOUNT_ID
    )
    root_trust = _trusts_by_role(transformed)[
        (
            "arn:aws:iam::000000000000:role/example-role-0",
            "arn:aws:iam::000000000000:root",
        )
    ]

    assert root_trust["has_condition"] is False
    assert root_trust["condition_keys"] == []
    assert root_trust["conditions"] is None


def test_empty_condition_block_is_not_a_condition():
    """`"Condition": {}` appears in real policies and must not flag the edge."""
    role = {
        "Path": "/",
        "RoleName": "empty-condition",
        "RoleId": "AROA00000000000000014",
        "Arn": "arn:aws:iam::000000000000:role/empty-condition",
        "CreateDate": datetime.datetime(2026, 1, 1, 0, 0, 1),
        "AssumeRolePolicyDocument": {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Action": "sts:AssumeRole",
                    "Effect": "Allow",
                    "Principal": {"AWS": "arn:aws:iam::000000000000:root"},
                    "Condition": {},
                },
            ],
        },
    }

    transformed = transform_role_trust_policies([role], TEST_ACCOUNT_ID)
    (trust,) = transformed.trust_relationships

    assert trust["has_condition"] is False
    assert trust["conditions"] is None


def test_not_principal_statement_is_skipped_without_raising(caplog):
    """A NotPrincipal-only statement is legal and must not abort the account sync."""
    role = {
        "Path": "/",
        "RoleName": "not-principal",
        "RoleId": "AROA00000000000000015",
        "Arn": "arn:aws:iam::000000000000:role/not-principal",
        "CreateDate": datetime.datetime(2026, 1, 1, 0, 0, 1),
        "AssumeRolePolicyDocument": {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Action": "sts:AssumeRole",
                    "Effect": "Allow",
                    "Principal": {"AWS": "arn:aws:iam::000000000000:root"},
                },
                {
                    "Action": "sts:AssumeRole",
                    "Effect": "Deny",
                    "NotPrincipal": {"AWS": "arn:aws:iam::000000000000:root"},
                },
            ],
        },
    }

    transformed = transform_role_trust_policies([role], TEST_ACCOUNT_ID)

    # The usable statement still produces its edge; the NotPrincipal one is skipped.
    assert [t["target_principal_arn"] for t in transformed.trust_relationships] == [
        "arn:aws:iam::000000000000:root"
    ]
    assert "NotPrincipal" in caplog.text


@pytest.mark.parametrize(
    "condition_blob",
    ["not json at all", "{unclosed", ""],
)
def test_unparseable_condition_fails_safe(condition_blob):
    """A Condition we cannot parse keeps the edge flagged rather than downgrading it.

    An empty value is falsy and means "no condition", so only the genuinely malformed
    blobs stay flagged.
    """
    role = {
        "Path": "/",
        "RoleName": "weird-condition",
        "RoleId": "AROA00000000000000016",
        "Arn": "arn:aws:iam::000000000000:role/weird-condition",
        "CreateDate": datetime.datetime(2026, 1, 1, 0, 0, 1),
        "AssumeRolePolicyDocument": {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Action": "sts:AssumeRole",
                    "Effect": "Allow",
                    "Principal": {"AWS": "arn:aws:iam::000000000000:root"},
                    "Condition": condition_blob,
                },
            ],
        },
    }

    transformed = transform_role_trust_policies([role], TEST_ACCOUNT_ID)
    (trust,) = transformed.trust_relationships

    if condition_blob:
        assert trust["has_condition"] is True
        assert trust["conditions"] is not None
    else:
        assert trust["has_condition"] is False
