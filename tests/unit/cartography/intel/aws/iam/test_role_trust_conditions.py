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


def test_statement_without_principal_raises():
    """Principal is required in a role trust policy, so its absence fails loudly.

    IAM rejects NotPrincipal in a role trust policy, so this shape cannot come back from
    the API; it is treated like any other missing required field.
    """
    role = {
        "Path": "/",
        "RoleName": "no-principal",
        "RoleId": "AROA00000000000000015",
        "Arn": "arn:aws:iam::000000000000:role/no-principal",
        "CreateDate": datetime.datetime(2026, 1, 1, 0, 0, 1),
        "AssumeRolePolicyDocument": {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Action": "sts:AssumeRole",
                    "Effect": "Deny",
                    "NotPrincipal": {"AWS": "arn:aws:iam::000000000000:root"},
                },
            ],
        },
    }

    with pytest.raises(KeyError):
        transform_role_trust_policies([role], TEST_ACCOUNT_ID)


def _role_with_statements(name, statements):
    return {
        "Path": "/",
        "RoleName": name,
        "RoleId": f"AROA{name.upper().replace('-', '')}",
        "Arn": f"arn:aws:iam::000000000000:role/{name}",
        "CreateDate": datetime.datetime(2026, 1, 1, 0, 0, 1),
        "AssumeRolePolicyDocument": {
            "Version": "2012-10-17",
            "Statement": statements,
        },
    }


ATTACKER_ARN = "arn:aws:iam::999999999999:role/attacker"
ROOT_ARN = "arn:aws:iam::000000000000:root"
SAML_PROVIDER_ARN = "arn:aws:iam::000000000000:saml-provider/ADFS"


def test_unconditional_deny_draws_no_edge():
    """Deny beats Allow in IAM evaluation, so a denied principal is not trusted."""
    role = _role_with_statements(
        "deny-only",
        [
            {
                "Effect": "Deny",
                "Principal": {"AWS": ATTACKER_ARN},
                "Action": "sts:AssumeRole",
            },
        ],
    )

    transformed = transform_role_trust_policies([role], TEST_ACCOUNT_ID)

    assert transformed.trust_relationships == []
    # A Deny is not evidence the account is trusted, so no stub is materialized.
    assert transformed.external_aws_accounts == []


def test_deny_overrides_allow_for_the_same_principal():
    role = _role_with_statements(
        "allow-then-deny",
        [
            {
                "Effect": "Allow",
                "Principal": {"AWS": [ATTACKER_ARN, ROOT_ARN]},
                "Action": "sts:AssumeRole",
            },
            {
                "Effect": "Deny",
                "Principal": {"AWS": ATTACKER_ARN},
                "Action": "sts:AssumeRole",
            },
        ],
    )

    transformed = transform_role_trust_policies([role], TEST_ACCOUNT_ID)

    assert [t["target_principal_arn"] for t in transformed.trust_relationships] == [
        ROOT_ARN
    ]


def test_conditional_deny_does_not_suppress_the_edge():
    """A Deny gated by a Condition only applies at request time, so the edge survives."""
    role = _role_with_statements(
        "conditional-deny",
        [
            {
                "Effect": "Allow",
                "Principal": {"AWS": ROOT_ARN},
                "Action": "sts:AssumeRole",
            },
            {
                "Effect": "Deny",
                "Principal": {"AWS": ROOT_ARN},
                "Action": "sts:AssumeRole",
                "Condition": {"Bool": {"aws:MultiFactorAuthPresent": "false"}},
            },
        ],
    )

    transformed = transform_role_trust_policies([role], TEST_ACCOUNT_ID)
    (trust,) = transformed.trust_relationships

    assert trust["target_principal_arn"] == ROOT_ARN
    # The Allow is unconditional, and the Deny's condition is not folded into it.
    assert trust["has_condition"] is False


@pytest.mark.parametrize(
    "action,expected_edge",
    [
        ("sts:AssumeRole", True),
        # Assume-role actions, but only an OIDC or SAML provider can call them.
        ("sts:AssumeRoleWithWebIdentity", False),
        ("sts:AssumeRoleWithSAML", False),
        ("sts:assumerole", True),  # IAM action names are case-insensitive
        ("sts:AssumeRole*", True),
        ("sts:*", True),
        ("*", True),
        ("sts:TagSession", False),
        ("sts:GetCallerIdentity", False),
        ("s3:GetObject", False),
    ],
)
def test_only_assume_role_actions_draw_an_edge(action, expected_edge):
    role = _role_with_statements(
        "action-check",
        [
            {
                "Effect": "Allow",
                "Principal": {"AWS": ROOT_ARN},
                "Action": action,
            },
        ],
    )

    transformed = transform_role_trust_policies([role], TEST_ACCOUNT_ID)

    assert bool(transformed.trust_relationships) is expected_edge


def test_action_list_with_one_assume_action_draws_an_edge():
    """sts:TagSession alongside a real assume action still makes the role assumable."""
    role = _role_with_statements(
        "tag-and-assume",
        [
            {
                "Effect": "Allow",
                "Principal": {"Federated": SAML_PROVIDER_ARN},
                "Action": ["sts:AssumeRoleWithSAML", "sts:TagSession"],
            },
        ],
    )

    transformed = transform_role_trust_policies([role], TEST_ACCOUNT_ID)

    assert [t["target_principal_arn"] for t in transformed.trust_relationships] == [
        SAML_PROVIDER_ARN
    ]


@pytest.mark.parametrize(
    "principal,action,expected_edge",
    [
        ({"AWS": ROOT_ARN}, "sts:AssumeRole", True),
        ({"AWS": ROOT_ARN}, "sts:AssumeRoleWithSAML", False),
        ({"AWS": ROOT_ARN}, "sts:AssumeRoleWithWebIdentity", False),
        ({"Service": "ec2.amazonaws.com"}, "sts:AssumeRole", True),
        ({"Service": "ec2.amazonaws.com"}, "sts:AssumeRoleWithWebIdentity", False),
        ({"Federated": SAML_PROVIDER_ARN}, "sts:AssumeRoleWithSAML", True),
        ({"Federated": SAML_PROVIDER_ARN}, "sts:AssumeRole", False),
        ({"Federated": SAML_PROVIDER_ARN}, "sts:AssumeRoleWithWebIdentity", False),
        (
            {"Federated": GITHUB_OIDC_PROVIDER_ARN},
            "sts:AssumeRoleWithWebIdentity",
            True,
        ),
        ({"Federated": GITHUB_OIDC_PROVIDER_ARN}, "sts:AssumeRole", False),
        ({"Federated": GITHUB_OIDC_PROVIDER_ARN}, "sts:AssumeRoleWithSAML", False),
        ({"Federated": "accounts.google.com"}, "sts:AssumeRoleWithWebIdentity", True),
        ({"Federated": "accounts.google.com"}, "sts:AssumeRoleWithSAML", False),
    ],
)
def test_an_edge_needs_an_assume_action_the_principal_can_call(
    principal, action, expected_edge
):
    """Each kind of principal can call one assume-role action, and only that one draws an edge."""
    role = _role_with_statements(
        "usable-action",
        [{"Effect": "Allow", "Principal": principal, "Action": action}],
    )

    transformed = transform_role_trust_policies([role], TEST_ACCOUNT_ID)

    assert bool(transformed.trust_relationships) is expected_edge


@pytest.mark.parametrize(
    "principal,not_action,expected_edge",
    [
        # Everything except s3:GetObject is allowed, which includes assuming the role.
        ({"AWS": ROOT_ARN}, "s3:GetObject", True),
        # Everything except sts:AssumeRole leaves the WebIdentity and SAML flavours,
        # which an OIDC provider can call and an AWS principal cannot.
        ({"AWS": ROOT_ARN}, "sts:AssumeRole", False),
        ({"Federated": GITHUB_OIDC_PROVIDER_ARN}, "sts:AssumeRole", True),
        # Nothing in the assume-role family is left.
        ({"AWS": ROOT_ARN}, "sts:AssumeRole*", False),
        ({"AWS": ROOT_ARN}, "sts:*", False),
        ({"AWS": ROOT_ARN}, "*", False),
    ],
)
def test_allow_not_action_is_resolved_over_the_assume_role_actions(
    principal, not_action, expected_edge
):
    """NotAction covers every action except the listed ones; only the assume-role ones count."""
    role = _role_with_statements(
        "not-action",
        [
            {
                "Effect": "Allow",
                "Principal": principal,
                "NotAction": not_action,
            },
        ],
    )

    transformed = transform_role_trust_policies([role], TEST_ACCOUNT_ID)

    assert bool(transformed.trust_relationships) is expected_edge


def test_deny_not_action_excluding_assume_role_keeps_the_edge():
    """A Deny on NotAction sts:AssumeRole denies everything except sts:AssumeRole."""
    role = _role_with_statements(
        "deny-not-action",
        [
            {
                "Effect": "Allow",
                "Principal": {"AWS": ROOT_ARN},
                "Action": "sts:AssumeRole",
            },
            {
                "Effect": "Deny",
                "Principal": {"AWS": ROOT_ARN},
                "NotAction": "sts:AssumeRole",
            },
        ],
    )

    transformed = transform_role_trust_policies([role], TEST_ACCOUNT_ID)

    assert [t["target_principal_arn"] for t in transformed.trust_relationships] == [
        ROOT_ARN
    ]


def test_deny_not_action_covering_assume_role_drops_the_edge():
    """A Deny on NotAction sts:TagSession denies every assume-role action."""
    role = _role_with_statements(
        "deny-not-action-all",
        [
            {
                "Effect": "Allow",
                "Principal": {"AWS": ROOT_ARN},
                "Action": "sts:AssumeRole",
            },
            {
                "Effect": "Deny",
                "Principal": {"AWS": ROOT_ARN},
                "NotAction": "sts:TagSession",
            },
        ],
    )

    transformed = transform_role_trust_policies([role], TEST_ACCOUNT_ID)

    assert transformed.trust_relationships == []


def test_deny_on_another_assume_action_keeps_the_edge():
    """Deny is tracked per action: denying the SAML flavour leaves sts:AssumeRole usable."""
    role = _role_with_statements(
        "deny-other-action",
        [
            {
                "Effect": "Allow",
                "Principal": {"AWS": ROOT_ARN},
                "Action": "sts:AssumeRole",
            },
            {
                "Effect": "Deny",
                "Principal": {"AWS": ROOT_ARN},
                "Action": "sts:AssumeRoleWithSAML",
            },
        ],
    )

    transformed = transform_role_trust_policies([role], TEST_ACCOUNT_ID)

    assert [t["target_principal_arn"] for t in transformed.trust_relationships] == [
        ROOT_ARN
    ]


def test_deny_of_every_granted_action_drops_the_edge():
    """A wildcard Allow is still fully denied when the Deny covers the whole family."""
    role = _role_with_statements(
        "deny-whole-family",
        [
            {
                "Effect": "Allow",
                "Principal": {"AWS": ROOT_ARN},
                "Action": "sts:*",
            },
            {
                "Effect": "Deny",
                "Principal": {"AWS": ROOT_ARN},
                "Action": "sts:AssumeRole*",
            },
        ],
    )

    transformed = transform_role_trust_policies([role], TEST_ACCOUNT_ID)

    assert transformed.trust_relationships == []


@pytest.mark.parametrize(
    "principal,deny_principal,denied_action",
    [
        ({"AWS": ATTACKER_ARN}, {"AWS": ATTACKER_ARN}, "sts:AssumeRole"),
        ({"Service": "ec2.amazonaws.com"}, "*", "sts:AssumeRole"),
        ({"Federated": SAML_PROVIDER_ARN}, "*", "sts:AssumeRoleWithSAML"),
        ({"Federated": GITHUB_OIDC_PROVIDER_ARN}, "*", "sts:AssumeRoleWithWebIdentity"),
    ],
)
def test_deny_of_the_only_action_a_principal_can_call_drops_its_edge(
    principal, deny_principal, denied_action
):
    """An Allow of every sts action leaves nothing once the one the principal can call is denied."""
    role = _role_with_statements(
        "deny-the-usable-action",
        [
            {"Effect": "Allow", "Principal": principal, "Action": "sts:*"},
            {"Effect": "Deny", "Principal": deny_principal, "Action": denied_action},
        ],
    )

    transformed = transform_role_trust_policies([role], TEST_ACCOUNT_ID)

    assert transformed.trust_relationships == []


def test_deny_of_everything_but_web_identity_leaves_only_the_oidc_trust():
    """Locking a role down to web identity also removes an AWS principal allowed sts:AssumeRole*."""
    role = _role_with_statements(
        "oidc-only",
        [
            {
                "Effect": "Allow",
                "Principal": {"AWS": ROOT_ARN},
                "Action": "sts:AssumeRole*",
            },
            {
                "Effect": "Allow",
                "Principal": {"Federated": GITHUB_OIDC_PROVIDER_ARN},
                "Action": "sts:AssumeRoleWithWebIdentity",
                "Condition": {
                    "StringEquals": {
                        "token.actions.githubusercontent.com:aud": "sts.amazonaws.com",
                    },
                },
            },
            {
                "Effect": "Deny",
                "Principal": "*",
                "NotAction": "sts:AssumeRoleWithWebIdentity",
            },
        ],
    )

    transformed = transform_role_trust_policies([role], TEST_ACCOUNT_ID)
    (trust,) = transformed.trust_relationships

    assert trust["target_principal_arn"] == GITHUB_OIDC_PROVIDER_ARN
    assert trust["has_condition"] is True


def test_deny_of_assume_role_to_everyone_leaves_only_the_saml_trust():
    """A statement naming an AWS principal and a SAML provider grants each its own action."""
    role = _role_with_statements(
        "sso-only",
        [
            {
                "Effect": "Allow",
                "Principal": {"AWS": ROOT_ARN, "Federated": SAML_PROVIDER_ARN},
                "Action": ["sts:AssumeRole", "sts:AssumeRoleWithSAML"],
            },
            {"Effect": "Deny", "Principal": "*", "Action": "sts:AssumeRole"},
        ],
    )

    transformed = transform_role_trust_policies([role], TEST_ACCOUNT_ID)

    assert [t["target_principal_arn"] for t in transformed.trust_relationships] == [
        SAML_PROVIDER_ARN
    ]


@pytest.mark.parametrize(
    "saml_condition",
    [None, {"StringEquals": {"SAML:aud": "https://signin.aws.amazon.com/saml"}}],
)
def test_a_statement_only_feeds_the_conditions_of_principals_that_can_use_it(
    saml_condition,
):
    """The root's only path is the MFA-gated sts:AssumeRole; the SAML statement is not one."""
    saml_statement = {
        "Effect": "Allow",
        "Principal": {"AWS": ROOT_ARN, "Federated": SAML_PROVIDER_ARN},
        "Action": "sts:AssumeRoleWithSAML",
    }
    if saml_condition:
        saml_statement["Condition"] = saml_condition
    role = _role_with_statements(
        "mfa-or-saml",
        [
            {
                "Effect": "Allow",
                "Principal": {"AWS": ROOT_ARN},
                "Action": "sts:AssumeRole",
                "Condition": {"Bool": {"aws:MultiFactorAuthPresent": "true"}},
            },
            saml_statement,
        ],
    )

    transformed = transform_role_trust_policies([role], TEST_ACCOUNT_ID)
    trusts = _trusts_by_role(transformed)

    root_trust = trusts[(role["Arn"], ROOT_ARN)]
    assert root_trust["has_condition"] is True
    assert root_trust["condition_keys"] == ["aws:MultiFactorAuthPresent"]
    assert json.loads(root_trust["conditions"]) == [
        {"Bool": {"aws:MultiFactorAuthPresent": "true"}}
    ]
    saml_trust = trusts[(role["Arn"], SAML_PROVIDER_ARN)]
    assert saml_trust["has_condition"] is (saml_condition is not None)


def test_an_ungated_grant_of_an_action_the_principal_cannot_call_keeps_the_gate():
    """A SAML provider cannot call sts:AssumeRole, so only the SAML:aud-gated statement counts."""
    role = _role_with_statements(
        "saml-gated",
        [
            {
                "Effect": "Allow",
                "Principal": {"Federated": SAML_PROVIDER_ARN},
                "Action": "sts:AssumeRoleWithSAML",
                "Condition": {
                    "StringEquals": {"SAML:aud": "https://signin.aws.amazon.com/saml"}
                },
            },
            {
                "Effect": "Allow",
                "Principal": {"Federated": SAML_PROVIDER_ARN},
                "Action": "sts:AssumeRole",
            },
        ],
    )

    transformed = transform_role_trust_policies([role], TEST_ACCOUNT_ID)
    (trust,) = transformed.trust_relationships

    assert trust["has_condition"] is True
    assert trust["condition_keys"] == ["SAML:aud"]


@pytest.mark.parametrize("wildcard", ["*", {"AWS": "*"}])
def test_unconditional_wildcard_principal_deny_drops_concrete_edges(wildcard):
    """The bare "*" and {"AWS": "*"} forms both match every principal, so the Deny applies to all."""
    role = _role_with_statements(
        "deny-everyone",
        [
            {
                "Effect": "Allow",
                "Principal": {"AWS": [ROOT_ARN, ATTACKER_ARN]},
                "Action": "sts:AssumeRole",
            },
            {
                "Effect": "Allow",
                "Principal": {"Federated": GITHUB_OIDC_PROVIDER_ARN},
                "Action": "sts:AssumeRoleWithWebIdentity",
            },
            {
                "Effect": "Deny",
                "Principal": wildcard,
                "Action": "sts:AssumeRole*",
            },
        ],
    )

    transformed = transform_role_trust_policies([role], TEST_ACCOUNT_ID)

    assert transformed.trust_relationships == []


def test_wildcard_principal_deny_on_another_action_keeps_the_edge():
    """A blanket Deny of the WebIdentity flavour does not touch an sts:AssumeRole trust."""
    role = _role_with_statements(
        "deny-everyone-web-identity",
        [
            {
                "Effect": "Allow",
                "Principal": {"AWS": ROOT_ARN},
                "Action": "sts:AssumeRole",
            },
            {
                "Effect": "Allow",
                "Principal": {"Federated": GITHUB_OIDC_PROVIDER_ARN},
                "Action": "sts:AssumeRoleWithWebIdentity",
            },
            {
                "Effect": "Deny",
                "Principal": "*",
                "Action": "sts:AssumeRoleWithWebIdentity",
            },
        ],
    )

    transformed = transform_role_trust_policies([role], TEST_ACCOUNT_ID)

    assert [t["target_principal_arn"] for t in transformed.trust_relationships] == [
        ROOT_ARN
    ]


@pytest.mark.parametrize(
    "account_principal", ["arn:aws:iam::999999999999:root", "999999999999"]
)
def test_unconditional_account_deny_drops_that_accounts_principals(account_principal):
    """A Deny naming an account covers its users and roles, not only its root user."""
    role = _role_with_statements(
        "deny-an-account",
        [
            {
                "Effect": "Allow",
                "Principal": {"AWS": [ROOT_ARN, ATTACKER_ARN]},
                "Action": "sts:AssumeRole",
            },
            {
                "Effect": "Deny",
                "Principal": {"AWS": account_principal},
                "Action": "sts:AssumeRole",
            },
        ],
    )

    transformed = transform_role_trust_policies([role], TEST_ACCOUNT_ID)

    assert [t["target_principal_arn"] for t in transformed.trust_relationships] == [
        ROOT_ARN
    ]


def test_account_deny_keeps_a_web_identity_trust():
    """A web identity is not a user or role of the account, so an account Deny leaves it."""
    role = _role_with_statements(
        "deny-own-account-keep-oidc",
        [
            {
                "Effect": "Allow",
                "Principal": {"Federated": GITHUB_OIDC_PROVIDER_ARN},
                "Action": "sts:AssumeRoleWithWebIdentity",
            },
            {
                "Effect": "Deny",
                "Principal": {"AWS": ROOT_ARN},
                "Action": "sts:AssumeRole*",
            },
        ],
    )

    transformed = transform_role_trust_policies([role], TEST_ACCOUNT_ID)

    assert [t["target_principal_arn"] for t in transformed.trust_relationships] == [
        GITHUB_OIDC_PROVIDER_ARN
    ]


def test_conditional_wildcard_principal_deny_is_not_applied():
    """A conditional Deny, wildcard or not, is resolved at request time and left alone."""
    role = _role_with_statements(
        "conditional-deny-everyone",
        [
            {
                "Effect": "Allow",
                "Principal": {"AWS": ROOT_ARN},
                "Action": "sts:AssumeRole",
            },
            {
                "Effect": "Deny",
                "Principal": "*",
                "Action": "sts:AssumeRole",
                "Condition": {"Bool": {"aws:MultiFactorAuthPresent": "false"}},
            },
        ],
    )

    transformed = transform_role_trust_policies([role], TEST_ACCOUNT_ID)

    assert [t["target_principal_arn"] for t in transformed.trust_relationships] == [
        ROOT_ARN
    ]


@pytest.mark.parametrize("wildcard", ["*", {"AWS": "*"}])
def test_wildcard_principal_allow_draws_no_edge_and_does_not_raise(wildcard):
    """A wildcard Allow has no principal node to point at; it is skipped, not a crash."""
    role = _role_with_statements(
        "allow-everyone",
        [
            {
                "Effect": "Allow",
                "Principal": wildcard,
                "Action": "sts:AssumeRole",
                "Condition": {"StringEquals": {"aws:PrincipalOrgID": "o-example"}},
            },
            {
                "Effect": "Allow",
                "Principal": {"AWS": ROOT_ARN},
                "Action": "sts:AssumeRole",
            },
        ],
    )

    transformed = transform_role_trust_policies([role], TEST_ACCOUNT_ID)

    assert [t["target_principal_arn"] for t in transformed.trust_relationships] == [
        ROOT_ARN
    ]


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
