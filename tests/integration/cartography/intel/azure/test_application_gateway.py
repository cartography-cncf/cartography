from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.azure.application_gateways as application_gateways
from tests.data.azure.application_gateway import MOCK_APPLICATION_GATEWAYS
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_SUBSCRIPTION_ID = "00-00-00-00"
TEST_UPDATE_TAG = 123456789


@patch(
    "cartography.intel.azure.application_gateways.get_application_gateways",
)
def test_sync_application_gateways(mock_get_ags, neo4j_session):
    """
    Test that we can correctly sync an Application Gateway and its child components and relationships.
    """
    # Arrange: Mock the single API call
    mock_get_ags.return_value = MOCK_APPLICATION_GATEWAYS

    # Create the prerequisite AzureSubscription node
    neo4j_session.run(
        "MERGE (s:AzureSubscription{id: $sub_id}) SET s.lastupdated = $tag",
        sub_id=TEST_SUBSCRIPTION_ID,
        tag=TEST_UPDATE_TAG,
    )

    # Create prerequisite nodes for cross-module relationships
    neo4j_session.run(
        "MERGE (n:AzureNetworkInterface{id: $nic_id}) SET n.lastupdated = $tag",
        nic_id="/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/networkInterfaces/my-appgw-nic",
        tag=TEST_UPDATE_TAG,
    )
    neo4j_session.run(
        "MERGE (p:AzurePublicIPAddress{id: $pip_id}) SET p.lastupdated = $tag, p.ip_address = '52.1.2.3'",
        pip_id="/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/publicIPAddresses/my-appgw-public-ip",
        tag=TEST_UPDATE_TAG,
    )
    neo4j_session.run(
        "MERGE (sn:AzureSubnet{id: $subnet_id}) SET sn.lastupdated = $tag",
        subnet_id="/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/virtualNetworks/my-vnet/subnets/my-appgw-subnet",
        tag=TEST_UPDATE_TAG,
    )
    # Backend public IP target (matched by AzurePublicIPAddress.ip_address)
    neo4j_session.run(
        "MERGE (p:AzurePublicIPAddress{id: $pip_id}) SET p.lastupdated = $tag, p.ip_address = '10.0.1.4'",
        pip_id="/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/publicIPAddresses/backend-public-ip",
        tag=TEST_UPDATE_TAG,
    )
    # Backend FQDN target via the DNSRecord ontology label (any provider works;
    # using a generic node here mimics what AWS/GCP/Cloudflare/Vercel DNS syncs
    # would produce).
    neo4j_session.run(
        "MERGE (d:DNSRecord{name: 'backend.example.com'}) " "SET d.lastupdated = $tag",
        tag=TEST_UPDATE_TAG,
    )

    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "AZURE_SUBSCRIPTION_ID": TEST_SUBSCRIPTION_ID,
    }

    # Act
    application_gateways.sync(
        neo4j_session,
        MagicMock(),
        TEST_SUBSCRIPTION_ID,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    # Assert Nodes for all four types (parent + 3 sub-resources, parallel to AzureLoadBalancer)
    ag = MOCK_APPLICATION_GATEWAYS[0]
    assert check_nodes(neo4j_session, "AzureApplicationGateway", ["id"]) == {
        (ag["id"],)
    }
    assert check_nodes(
        neo4j_session,
        "AzureApplicationGatewayFrontendIPConfiguration",
        ["id"],
    ) == {(ag["frontend_ip_configurations"][0]["id"],)}
    assert check_nodes(neo4j_session, "AzureApplicationGatewayBackendPool", ["id"]) == {
        (ag["backend_address_pools"][0]["id"],)
    }
    assert check_nodes(neo4j_session, "AzureApplicationGatewayRule", ["id"]) == {
        (ag["request_routing_rules"][0]["id"],),
        (ag["request_routing_rules"][1]["id"],),
    }

    # Confirm the LoadBalancer ontology label is applied to the parent
    assert check_nodes(neo4j_session, "LoadBalancer", ["id"]) >= {(ag["id"],)}

    # Capture IDs for relationship assertions
    ag_id = ag["id"]
    frontend_ip_id = ag["frontend_ip_configurations"][0]["id"]
    backend_pool_id = ag["backend_address_pools"][0]["id"]
    rule_id = ag["request_routing_rules"][0]["id"]
    path_rule_id = ag["request_routing_rules"][1]["id"]
    subnet_id = "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/virtualNetworks/my-vnet/subnets/my-appgw-subnet"
    pip_id = "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/publicIPAddresses/my-appgw-public-ip"
    nic_id = "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/networkInterfaces/my-appgw-nic"

    # Test Parent Relationships (:RESOURCE and :CONTAINS)
    expected_parent_rels = {
        (TEST_SUBSCRIPTION_ID, ag_id),
        (ag_id, frontend_ip_id),
        (ag_id, backend_pool_id),
        (ag_id, rule_id),
        (ag_id, path_rule_id),
    }
    actual_parent_rels = check_rels(
        neo4j_session,
        "AzureSubscription",
        "id",
        "AzureApplicationGateway",
        "id",
        "RESOURCE",
    )
    actual_parent_rels.update(
        check_rels(
            neo4j_session,
            "AzureApplicationGateway",
            "id",
            "AzureApplicationGatewayFrontendIPConfiguration",
            "id",
            "CONTAINS",
        )
    )
    actual_parent_rels.update(
        check_rels(
            neo4j_session,
            "AzureApplicationGateway",
            "id",
            "AzureApplicationGatewayBackendPool",
            "id",
            "CONTAINS",
        )
    )
    actual_parent_rels.update(
        check_rels(
            neo4j_session,
            "AzureApplicationGateway",
            "id",
            "AzureApplicationGatewayRule",
            "id",
            "CONTAINS",
        )
    )
    assert actual_parent_rels == expected_parent_rels

    # Application Gateway -> Subnet
    assert check_rels(
        neo4j_session,
        "AzureApplicationGateway",
        "id",
        "AzureSubnet",
        "id",
        "IN_SUBNET",
        rel_direction_right=True,
    ) == {(ag_id, subnet_id)}

    # FrontendIP -> PublicIP (ASSOCIATED_WITH)
    assert check_rels(
        neo4j_session,
        "AzureApplicationGatewayFrontendIPConfiguration",
        "id",
        "AzurePublicIPAddress",
        "id",
        "ASSOCIATED_WITH",
        rel_direction_right=True,
    ) == {(frontend_ip_id, pip_id)}

    # BackendPool -> NIC (ROUTES_TO)
    assert check_rels(
        neo4j_session,
        "AzureApplicationGatewayBackendPool",
        "id",
        "AzureNetworkInterface",
        "id",
        "ROUTES_TO",
        rel_direction_right=True,
    ) == {(backend_pool_id, nic_id)}

    # BackendPool -> AzurePublicIPAddress (ROUTES_TO via ip_address match)
    backend_pip_id = "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Network/publicIPAddresses/backend-public-ip"
    assert check_rels(
        neo4j_session,
        "AzureApplicationGatewayBackendPool",
        "id",
        "AzurePublicIPAddress",
        "id",
        "ROUTES_TO",
        rel_direction_right=True,
    ) == {(backend_pool_id, backend_pip_id)}

    # BackendPool -> DNSRecord (ROUTES_TO via FQDN match against the cross-provider
    # ontology label)
    dns_routes = neo4j_session.run(
        """
        MATCH (p:AzureApplicationGatewayBackendPool {id: $pool_id})
              -[:ROUTES_TO]->(d:DNSRecord)
        RETURN d.name AS name
        """,
        pool_id=backend_pool_id,
    )
    assert {row["name"] for row in dns_routes} == {"backend.example.com"}

    # Rule wiring (Basic + PathBasedRouting both produce edges, parallel to AzureLoadBalancerRule)
    assert check_rels(
        neo4j_session,
        "AzureApplicationGatewayRule",
        "id",
        "AzureApplicationGatewayFrontendIPConfiguration",
        "id",
        "USES_FRONTEND_IP",
        rel_direction_right=True,
    ) == {(rule_id, frontend_ip_id), (path_rule_id, frontend_ip_id)}
    # Only the Basic rule emits ROUTES_TO; PathBasedRouting routes via a
    # url_path_map whose path rules can target different backends, so we keep
    # `url_path_map_id` as a property pointer and skip the edge until path
    # rules are modelled explicitly.
    assert check_rels(
        neo4j_session,
        "AzureApplicationGatewayRule",
        "id",
        "AzureApplicationGatewayBackendPool",
        "id",
        "ROUTES_TO",
        rel_direction_right=True,
    ) == {(rule_id, backend_pool_id)}

    # Verify listener + backend settings were folded onto the Rule node
    rule_props = neo4j_session.run(
        """
        MATCH (r:AzureApplicationGatewayRule {id: $id})
        RETURN r.listener_protocol AS lp, r.listener_port AS lport,
               r.backend_protocol AS bp, r.backend_port AS bport,
               r.listener_id IS NOT NULL AS has_lid,
               r.backend_http_settings_id IS NOT NULL AS has_sid
        """,
        id=rule_id,
    ).single()
    assert rule_props["lp"] == "Https"
    assert rule_props["lport"] == 443
    assert rule_props["bp"] == "Https"
    assert rule_props["bport"] == 443
    assert rule_props["has_lid"]
    assert rule_props["has_sid"]

    # PathBasedRouting rule keeps url_path_map_id as a pointer but does not
    # synthesize backend_* fields from the path map's defaults.
    path_rule_props = neo4j_session.run(
        """
        MATCH (r:AzureApplicationGatewayRule {id: $id})
        RETURN r.url_path_map_id AS pmid,
               r.backend_http_settings_id AS sid,
               r.backend_protocol AS bp,
               r.backend_port AS bport
        """,
        id=path_rule_id,
    ).single()
    assert path_rule_props["pmid"] is not None
    assert path_rule_props["sid"] is None
    assert path_rule_props["bp"] is None
    assert path_rule_props["bport"] is None


def test_load_application_gateway_tags(neo4j_session):
    """
    Test that tags are correctly loaded and linked to Azure Application Gateways.
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
    transformed_ags = application_gateways.transform_application_gateways(
        MOCK_APPLICATION_GATEWAYS,
    )

    # Load Application Gateways so they exist to be tagged
    application_gateways.load_application_gateways(
        neo4j_session, transformed_ags, TEST_SUBSCRIPTION_ID, TEST_UPDATE_TAG
    )

    # 2. Act: Load the tags
    application_gateways.load_application_gateway_tags(
        neo4j_session,
        TEST_SUBSCRIPTION_ID,
        transformed_ags,
        TEST_UPDATE_TAG,
    )

    # 3. Assert: Check for the 2 unique tags
    expected_tags = {
        f"{TEST_SUBSCRIPTION_ID}|env:prod",
        f"{TEST_SUBSCRIPTION_ID}|service:application-gateway",
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
    ag_id = MOCK_APPLICATION_GATEWAYS[0]["id"]

    expected_rels = {
        (ag_id, f"{TEST_SUBSCRIPTION_ID}|env:prod"),
        (ag_id, f"{TEST_SUBSCRIPTION_ID}|service:application-gateway"),
    }

    result = neo4j_session.run(
        """
        MATCH (ag:AzureApplicationGateway)-[:TAGGED]->(t:AzureTag)
        RETURN ag.id, t.id
        """
    )
    actual_rels = {(r["ag.id"], r["t.id"]) for r in result}
    assert actual_rels == expected_rels
