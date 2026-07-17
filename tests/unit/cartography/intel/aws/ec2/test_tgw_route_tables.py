from cartography.intel.aws.ec2 import tgw_route_tables
from cartography.models.aws.ec2.tgw_route_tables import (
    AWSTransitGatewayRouteSchema,
    AWSTransitGatewayRouteTableAssociationSchema,
    AWSTransitGatewayRouteTablePropagationSchema,
    AWSTransitGatewayRouteTableSchema,
)


def test_transform_tgw_route_tables_empty():
    # Arrange / Act
    rts, routes = tgw_route_tables.transform_tgw_route_tables([])
    # Assert
    assert rts == []
    assert routes == []


def test_transform_tgw_route_tables_sample():
    # Arrange
    sample = [
        {
            "TransitGatewayRouteTableId": "tgw-rtb-1",
            "TransitGatewayId": "tgw-1",
            "State": "available",
            "Region": "us-east-1",
            "Routes": [
                {
                    "DestinationCidrBlock": "10.0.0.0/16",
                    "State": "active",
                    "Origin": "Create",
                    "TransitGatewayAttachmentId": "tgw-attach-1",
                }
            ],
        }
    ]
    # Act
    rts, routes = tgw_route_tables.transform_tgw_route_tables(sample)
    # Assert
    assert len(rts) == 1
    assert len(routes) == 1
    assert rts[0]["TransitGatewayRouteTableId"] == "tgw-rtb-1"
    assert routes[0]["destination_cidr_block"] == "10.0.0.0/16"


def test_transform_route_table_includes_lowercase_tgw_id():
    """The TGW->route-table CONTAINS matcher reads PropertyRef("transit_gateway_id");
    the route-table dict must carry that lowercase key or the edge matches nothing."""
    # Arrange
    sample = [
        {
            "TransitGatewayRouteTableId": "tgw-rtb-1",
            "TransitGatewayId": "tgw-1",
            "State": "available",
            "Region": "us-east-1",
        }
    ]
    # Act
    rts, _ = tgw_route_tables.transform_tgw_route_tables(sample)
    # Assert
    assert rts[0]["transit_gateway_id"] == "tgw-1"


def test_transform_route_target_from_nested_attachments():
    """Route target comes from the nested TransitGatewayAttachments[] list, not a
    top-level field; without this ROUTES_TO_TGW_ATTACHMENT matches nothing."""
    # Arrange
    sample = [
        {
            "TransitGatewayRouteTableId": "tgw-rtb-1",
            "TransitGatewayId": "tgw-1",
            "Region": "us-east-1",
            "Routes": [
                {
                    "DestinationCidrBlock": "10.100.0.0/16",
                    "State": "active",
                    "TransitGatewayAttachments": [
                        {
                            "TransitGatewayAttachmentId": "tgw-attach-9",
                            "ResourceId": "vpc-1",
                            "ResourceType": "vpc",
                        }
                    ],
                }
            ],
        }
    ]
    # Act
    _, routes = tgw_route_tables.transform_tgw_route_tables(sample)
    # Assert
    assert routes[0]["target"] == "tgw-attach-9"


def test_transform_associations_populates_id_and_route_table_id():
    """The get_ association API omits both TransitGatewayRouteTableAssociationId
    and TransitGatewayRouteTableId; the fetch helper injects them. If either is
    null the loader drops the record (0 association nodes). This asserts the
    transform preserves the injected id/route_table_id and reads flat State."""
    # Arrange: shape as the fetch helper emits it (ids already injected)
    data = [
        {
            "TransitGatewayRouteTableId": "tgw-rtb-1",
            "TransitGatewayRouteTableAssociationId": "tgw-rtb-1|tgw-attach-1",
            "TransitGatewayAttachmentId": "tgw-attach-1",
            "ResourceId": "vpc-1",
            "ResourceType": "vpc",
            "State": "associated",
        }
    ]
    # Act
    out = tgw_route_tables.transform_tgw_route_table_associations(data)
    # Assert
    assert len(out) == 1
    assert out[0]["id"] == "tgw-rtb-1|tgw-attach-1"
    assert out[0]["route_table_id"] == "tgw-rtb-1"
    assert out[0]["attachment_id"] == "tgw-attach-1"
    assert out[0]["state"] == "associated"


def test_transform_associations_reads_nested_association_state():
    """describe_ responses nest state under AssociationState.State; support it."""
    # Arrange
    data = [
        {
            "TransitGatewayRouteTableId": "tgw-rtb-1",
            "TransitGatewayRouteTableAssociationId": "assoc-1",
            "TransitGatewayAttachmentId": "tgw-attach-1",
            "AssociationState": {"State": "associated"},
        }
    ]
    # Act
    out = tgw_route_tables.transform_tgw_route_table_associations(data)
    # Assert
    assert out[0]["state"] == "associated"


def test_transform_associations_dedups_by_id():
    """The same association fetched more than once must not produce duplicates
    (guards against the fan-out / duplication class of bug)."""
    # Arrange: same id appears twice
    data = [
        {
            "TransitGatewayRouteTableId": "tgw-rtb-1",
            "TransitGatewayRouteTableAssociationId": "tgw-rtb-1|tgw-attach-1",
            "TransitGatewayAttachmentId": "tgw-attach-1",
            "State": "associated",
        },
        {
            "TransitGatewayRouteTableId": "tgw-rtb-1",
            "TransitGatewayRouteTableAssociationId": "tgw-rtb-1|tgw-attach-1",
            "TransitGatewayAttachmentId": "tgw-attach-1",
            "State": "associated",
        },
    ]
    # Act
    out = tgw_route_tables.transform_tgw_route_table_associations(data)
    # Assert
    assert len(out) == 1


def test_all_tgw_node_schemas_have_account_sub_resource():
    """Every TGW route-table node must be owned by an AWSAccount so account-scoped
    cleanup works and the node is reachable from the account (guards against the
    unowned-root-node failure)."""
    # Arrange
    schemas = [
        AWSTransitGatewayRouteTableSchema(),
        AWSTransitGatewayRouteSchema(),
        AWSTransitGatewayRouteTableAssociationSchema(),
        AWSTransitGatewayRouteTablePropagationSchema(),
    ]
    # Act / Assert
    for schema in schemas:
        assert schema.sub_resource_relationship is not None, schema.label
        assert (
            schema.sub_resource_relationship.target_node_label == "AWSAccount"
        ), schema.label


def test_tgw_route_table_relationships_declared_inline():
    """Relationships must be carried by the schema (regression for the frozen-
    dataclass append that silently dropped the route-table -> TGW and
    route -> route-table edges)."""
    # Arrange
    rt_rels = {
        r.rel_label
        for r in AWSTransitGatewayRouteTableSchema().other_relationships.rels
    }
    route_rels = {
        r.rel_label for r in AWSTransitGatewayRouteSchema().other_relationships.rels
    }
    # Assert
    assert "CONTAINS" in rt_rels
    assert {"HAS_ROUTE", "ROUTES_TO_TGW", "ROUTES_TO_TGW_ATTACHMENT"} <= route_rels
