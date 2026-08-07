import copy
from unittest.mock import patch

import requests

import cartography.intel.anthropic.federation
import tests.data.anthropic.federation
from tests.integration.cartography.intel.anthropic.test_organization import (
    _ensure_local_neo4j_has_test_organization,
)
from tests.integration.cartography.intel.anthropic.test_serviceaccounts import (
    _ensure_local_neo4j_has_test_service_accounts,
)
from tests.integration.cartography.intel.anthropic.test_workspaces import (
    _ensure_local_neo4j_has_test_workspaces,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_ORG_ID = "8834c225-ea27-405a-aea9-5ed5f07f4858"
TEST_WORKSPACE_ID = "wrkspc_01JwQvzr7rXLA5AGx3HKfFUJ"


@patch.object(
    cartography.intel.anthropic.federation,
    "get_rule_workspaces",
    side_effect=lambda _session, _url, rule_id: (
        tests.data.anthropic.federation.ANTHROPIC_FEDERATION_RULE_WORKSPACES[rule_id]
    ),
)
@patch.object(
    cartography.intel.anthropic.federation,
    "get_rules",
    return_value=copy.deepcopy(
        tests.data.anthropic.federation.ANTHROPIC_FEDERATION_RULES
    ),
)
@patch.object(
    cartography.intel.anthropic.federation,
    "get_issuers",
    return_value=copy.deepcopy(
        tests.data.anthropic.federation.ANTHROPIC_FEDERATION_ISSUERS
    ),
)
def test_load_anthropic_federation(
    mock_issuers, mock_rules, mock_rule_workspaces, neo4j_session
):
    """
    Ensure that federation issuers and rules get loaded and wired to each other
    """
    # Arrange
    api_session = requests.Session()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "BASE_URL": "https://api.anthropic.com/v1",
        "ORG_ID": TEST_ORG_ID,
    }
    _ensure_local_neo4j_has_test_organization(neo4j_session)
    _ensure_local_neo4j_has_test_workspaces(neo4j_session)
    _ensure_local_neo4j_has_test_service_accounts(neo4j_session)

    # Act
    cartography.intel.anthropic.federation.sync(
        neo4j_session,
        api_session,
        common_job_parameters,
    )

    # Assert issuers exist, with the jwks union flattened. The second issuer has key
    # polling disabled and failing fetches, which is the interesting posture.
    expected_nodes = {
        (
            "fdis_01Ab2Cd3Ef4Gh5Ij6Kl7Mn8Op",
            "github-actions",
            True,
            "discovery",
            None,
            0,
        ),
        (
            "fdis_01Zy9Xw8Vu7Ts6Rq5Po4Nm3Lk",
            "springfield-k8s",
            False,
            "explicit_url",
            "https://kubernetes.springfield.corp/openid/v1/jwks",
            3,
        ),
    }
    assert (
        check_nodes(
            neo4j_session,
            "AnthropicFederationIssuer",
            [
                "id",
                "name",
                "check_jti",
                "jwks_type",
                "jwks_url",
                "poll_status_consecutive_failures",
            ],
        )
        == expected_nodes
    )

    # Assert rules exist, with the matchers flattened. The wildcard subject_prefix on
    # the second rule is what makes fork pull requests able to mint a token.
    expected_nodes = {
        (
            "fdrl_01Qw2Er3Ty4Ui5Op6As7Df8Gh",
            "cartography-collector",
            "org:admin",
            "system:serviceaccount:security:cartography",
            False,
        ),
        (
            "fdrl_01Hj2Kl3Zx4Cv5Bn6Mq7Wt8Ry",
            "ci-inference",
            "workspace:developer",
            "repo:springfield/reactor-control:*",
            True,
        ),
    }
    assert (
        check_nodes(
            neo4j_session,
            "AnthropicFederationRule",
            [
                "id",
                "name",
                "oauth_scope",
                "match_subject_prefix",
                "applies_to_all_workspaces",
            ],
        )
        == expected_nodes
    )

    # Assert the claims map was flattened onto the rule that carries one. Queried
    # directly because check_nodes cannot hash a list-valued property.
    claims_by_rule = {
        record["id"]: record["match_claims"]
        for record in neo4j_session.run(
            "MATCH (r:AnthropicFederationRule) RETURN r.id AS id, "
            "r.match_claims AS match_claims"
        )
    }
    assert claims_by_rule == {
        "fdrl_01Qw2Er3Ty4Ui5Op6As7Df8Gh": ["namespace=security"],
        "fdrl_01Hj2Kl3Zx4Cv5Bn6Mq7Wt8Ry": [],
    }

    # Assert issuers and rules are linked to the correct org
    for label in ("AnthropicFederationIssuer", "AnthropicFederationRule"):
        assert {
            org_id
            for _, org_id in check_rels(
                neo4j_session,
                label,
                "id",
                "AnthropicOrganization",
                "id",
                "RESOURCE",
                rel_direction_right=False,
            )
        } == {TEST_ORG_ID}

    # Assert each rule trusts the right issuer
    expected_rels = {
        ("fdrl_01Qw2Er3Ty4Ui5Op6As7Df8Gh", "fdis_01Zy9Xw8Vu7Ts6Rq5Po4Nm3Lk"),
        ("fdrl_01Hj2Kl3Zx4Cv5Bn6Mq7Wt8Ry", "fdis_01Ab2Cd3Ef4Gh5Ij6Kl7Mn8Op"),
    }
    assert (
        check_rels(
            neo4j_session,
            "AnthropicFederationRule",
            "id",
            "AnthropicFederationIssuer",
            "id",
            "AUTHENTICATED_BY",
            rel_direction_right=True,
        )
        == expected_rels
    )

    # Assert each rule mints tokens acting as the right service account. This is the
    # escalation path: rule -> service account -> organization_role.
    expected_rels = {
        ("fdrl_01Qw2Er3Ty4Ui5Op6As7Df8Gh", "svac_01Pq8WeRtYuIoPaSdFgHjKlM"),
        ("fdrl_01Hj2Kl3Zx4Cv5Bn6Mq7Wt8Ry", "svac_01Nb5RtYuIoPaSdFgHjKlZxC"),
    }
    assert (
        check_rels(
            neo4j_session,
            "AnthropicFederationRule",
            "id",
            "AnthropicServiceAccount",
            "id",
            "ASSUMES",
            rel_direction_right=True,
        )
        == expected_rels
    )

    # Assert only the explicitly enabled workspace is edged
    expected_rels = {
        ("fdrl_01Hj2Kl3Zx4Cv5Bn6Mq7Wt8Ry", TEST_WORKSPACE_ID),
    }
    assert (
        check_rels(
            neo4j_session,
            "AnthropicFederationRule",
            "id",
            "AnthropicWorkspace",
            "id",
            "ENABLED_ON",
            rel_direction_right=True,
        )
        == expected_rels
    )
