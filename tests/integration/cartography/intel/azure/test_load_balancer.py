from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.azure.load_balancers as load_balancer
from tests.data.azure.load_balancer import MOCK_LOAD_BALANCERS
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_SUBSCRIPTION_ID = "00-00-00-00"
TEST_UPDATE_TAG = 123456789


@patch("cartography.intel.azure.load_balancers.get_load_balancers")
def test_sync_load_balancers(mock_get_lbs, neo4j_session):
    """
    Test that we can correctly sync a Load Balancer and its child components and relationships.
    """
    # Arrange: Mock the single API call
    mock_get_lbs.return_value = MOCK_LOAD_BALANCERS

    # Create the prerequisite AzureSubscription node
    neo4j_session.run(
        "MERGE (s:AzureSubscription{id: $sub_id}) SET s.lastupdated = $tag",
        sub_id=TEST_SUBSCRIPTION_ID,
        tag=TEST_UPDATE_TAG,
    )

    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "AZURE_SUBSCRIPTION_ID": TEST_SUBSCRIPTION_ID,
    }

    # Act
    load_balancer.sync(
        neo4j_session,
        MagicMock(),
        TEST_SUBSCRIPTION_ID,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    # Assert Nodes for all five types
    assert check_nodes(neo4j_session, "AzureLoadBalancer", ["id"]) == {
        (MOCK_LOAD_BALANCERS[0]["id"],)
    }
    assert check_nodes(
        neo4j_session, "AzureLoadBalancerFrontendIPConfiguration", ["id"]
    ) == {(MOCK_LOAD_BALANCERS[0]["frontend_ip_configurations"][0]["id"],)}
    assert check_nodes(neo4j_session, "AzureLoadBalancerBackendPool", ["id"]) == {
        (MOCK_LOAD_BALANCERS[0]["backend_address_pools"][0]["id"],)
    }
    assert check_nodes(neo4j_session, "AzureLoadBalancerRule", ["id"]) == {
        (MOCK_LOAD_BALANCERS[0]["load_balancing_rules"][0]["id"],)
    }
    assert check_nodes(neo4j_session, "AzureLoadBalancerInboundNatRule", ["id"]) == {
        (MOCK_LOAD_BALANCERS[0]["inbound_nat_rules"][0]["id"],)
    }

    # Assert Relationships
    lb_id = MOCK_LOAD_BALANCERS[0]["id"]
    frontend_ip_id = MOCK_LOAD_BALANCERS[0]["frontend_ip_configurations"][0]["id"]
    backend_pool_id = MOCK_LOAD_BALANCERS[0]["backend_address_pools"][0]["id"]
    rule_id = MOCK_LOAD_BALANCERS[0]["load_balancing_rules"][0]["id"]
    nat_rule_id = MOCK_LOAD_BALANCERS[0]["inbound_nat_rules"][0]["id"]

    # Test Parent Relationships (:RESOURCE and :CONTAINS)
    expected_parent_rels = {
        (TEST_SUBSCRIPTION_ID, lb_id),
        (lb_id, frontend_ip_id),
        (lb_id, backend_pool_id),
        (lb_id, rule_id),
        (lb_id, nat_rule_id),
    }
    actual_parent_rels = check_rels(
        neo4j_session, "AzureSubscription", "id", "AzureLoadBalancer", "id", "RESOURCE"
    )
    actual_parent_rels.update(
        check_rels(
            neo4j_session,
            "AzureLoadBalancer",
            "id",
            "AzureLoadBalancerFrontendIPConfiguration",
            "id",
            "CONTAINS",
        )
    )
    actual_parent_rels.update(
        check_rels(
            neo4j_session,
            "AzureLoadBalancer",
            "id",
            "AzureLoadBalancerBackendPool",
            "id",
            "CONTAINS",
        )
    )
    actual_parent_rels.update(
        check_rels(
            neo4j_session,
            "AzureLoadBalancer",
            "id",
            "AzureLoadBalancerRule",
            "id",
            "CONTAINS",
        )
    )
    actual_parent_rels.update(
        check_rels(
            neo4j_session,
            "AzureLoadBalancer",
            "id",
            "AzureLoadBalancerInboundNatRule",
            "id",
            "CONTAINS",
        )
    )
    assert actual_parent_rels == expected_parent_rels

    # Test Data Flow Relationships
    assert check_rels(
        neo4j_session,
        "AzureLoadBalancerRule",
        "id",
        "AzureLoadBalancerFrontendIPConfiguration",
        "id",
        "USES_FRONTEND_IP",
    ) == {(rule_id, frontend_ip_id)}
    assert check_rels(
        neo4j_session,
        "AzureLoadBalancerRule",
        "id",
        "AzureLoadBalancerBackendPool",
        "id",
        "ROUTES_TO",
    ) == {(rule_id, backend_pool_id)}


def test_load_load_balancer_tags(neo4j_session):
    """
    Test that tags are correctly loaded and linked to Azure Load Balancers.
    """
    # 1. Arrange: Create the prerequisite AzureSubscription node
    neo4j_session.run(
        """
        MERGE (s:AzureSubscription{id: $sub_id})
        SET s.lastupdated = $update_tag
        """,
        sub_id=TEST_SUBSCRIPTION_ID,
        update_tag=TEST_UPDATE_TAG,
    )

    # Transform the data first to include tags
    transformed_lbs = load_balancer.transform_load_balancers(MOCK_LOAD_BALANCERS)

    # Load Load Balancers so they exist to be tagged
    load_balancer.load_load_balancers(
        neo4j_session, transformed_lbs, TEST_SUBSCRIPTION_ID, TEST_UPDATE_TAG
    )

    # 2. Act: Load the tags
    load_balancer.load_load_balancer_tags(
        neo4j_session,
        TEST_SUBSCRIPTION_ID,
        transformed_lbs,
        TEST_UPDATE_TAG,
    )

    # 3. Assert: Check for the 2 unique tags
    expected_tags = {
        f"{TEST_SUBSCRIPTION_ID}|env:prod",
        f"{TEST_SUBSCRIPTION_ID}|service:load-balancer",
    }

    tag_nodes = neo4j_session.run(
        """
        MATCH (t:AzureTag)
        WHERE t.id STARTS WITH $sub_id
        RETURN t.id
        """,
        sub_id=TEST_SUBSCRIPTION_ID,
    )
    actual_tags = {n["t.id"] for n in tag_nodes}
    assert actual_tags == expected_tags

    # 4. Assert: Check the relationships
    lb_id = MOCK_LOAD_BALANCERS[0]["id"]

    expected_rels = {
        (lb_id, f"{TEST_SUBSCRIPTION_ID}|env:prod"),
        (lb_id, f"{TEST_SUBSCRIPTION_ID}|service:load-balancer"),
    }

    result = neo4j_session.run(
        """
        MATCH (lb:AzureLoadBalancer)-[:TAGGED]->(t:AzureTag)
        RETURN lb.id, t.id
        """
    )
    actual_rels = {(r["lb.id"], r["t.id"]) for r in result}
    assert actual_rels == expected_rels
