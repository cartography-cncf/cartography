# Association/Propagation helpers

def get_transit_gateway_route_table_associations(boto3_session: boto3.session.Session, region: str) -> list[dict[str, Any]]:
    client = create_boto3_client(boto3_session, "ec2", region_name=region, config=get_botocore_config())
    associations: list[dict[str, Any]] = []
    try:
        paginator = client.get_paginator("describe_transit_gateway_route_table_associations")
        for page in paginator.paginate():
            associations.extend(page.get("TransitGatewayRouteTableAssociations", []))
    except botocore.exceptions.ClientError as e:
        logger.warning(
            "Could not retrieve Transit Gateway route table associations due to boto3 error %s: %s. Skipping.",
            e.response.get("Error", {}).get("Code"),
            e.response.get("Error", {}).get("Message"),
        )
    return associations


def transform_tgw_route_table_associations(data: list[dict[str, Any]]) -> list[dict[str, Any]]:
    transformed: list[dict[str, Any]] = []
    for assoc in data:
        transformed.append(
            {
                "id": assoc.get("TransitGatewayRouteTableAssociationId"),
                "route_table_id": assoc.get("TransitGatewayRouteTableId"),
                "attachment_id": assoc.get("TransitGatewayAttachmentId"),
                "resource_id": assoc.get("ResourceId"),
                "resource_type": assoc.get("ResourceType"),
                "state": assoc.get("AssociationState", {}).get("State"),
            }
        )
    return transformed


def load_transit_gateway_route_table_associations(neo4j_session: neo4j.Session, data: list[dict[str, Any]], region: str, current_aws_account_id: str, update_tag: int) -> None:
    # For now load as simple nodes/relationships using a custom query; this can be replaced with model-driven load later
    for item in data:
        run_write_query(
            neo4j_session,
            """
            MERGE (a:AWSTransitGatewayRouteTableAssociation{id: $id})
            SET a.route_table_id = $route_table_id, a.attachment_id = $attachment_id, a.resource_id = $resource_id, a.resource_type = $resource_type, a.state = $state, a.Region = $Region, a.lastupdated = $lastupdated
            WITH a
            MATCH (rt:AWSTransitGatewayRouteTable{TransitGatewayRouteTableId: $route_table_id})
            MERGE (rt)<-[:RESOURCE]-(a)
            """,
            id=item.get("id"),
            route_table_id=item.get("route_table_id"),
            attachment_id=item.get("attachment_id"),
            resource_id=item.get("resource_id"),
            resource_type=item.get("resource_type"),
            state=item.get("state"),
            Region=region,
            lastupdated=update_tag,
        )


def get_transit_gateway_route_table_propagations(boto3_session: boto3.session.Session, region: str) -> list[dict[str, Any]]:
    client = create_boto3_client(boto3_session, "ec2", region_name=region, config=get_botocore_config())
    props: list[dict[str, Any]] = []
    try:
        paginator = client.get_paginator("describe_transit_gateway_route_table_propagations")
        for page in paginator.paginate():
            props.extend(page.get("TransitGatewayRouteTablePropagations", []))
    except botocore.exceptions.ClientError as e:
        logger.warning(
            "Could not retrieve Transit Gateway route table propagations due to boto3 error %s: %s. Skipping.",
            e.response.get("Error", {}).get("Code"),
            e.response.get("Error", {}).get("Message"),
        )
    return props


def transform_tgw_route_table_propagations(data: list[dict[str, Any]]) -> list[dict[str, Any]]:
    transformed: list[dict[str, Any]] = []
    for p in data:
        transformed.append(
            {
                "id": p.get("TransitGatewayRouteTablePropagationId"),
                "route_table_id": p.get("TransitGatewayRouteTableId"),
                "attachment_id": p.get("TransitGatewayAttachmentId"),
                "state": p.get("State"),
            }
        )
    return transformed


def load_transit_gateway_route_table_propagations(neo4j_session: neo4j.Session, data: list[dict[str, Any]], region: str, current_aws_account_id: str, update_tag: int) -> None:
    for item in data:
        run_write_query(
            neo4j_session,
            """
            MERGE (p:AWSTransitGatewayRouteTablePropagation{id: $id})
            SET p.route_table_id = $route_table_id, p.attachment_id = $attachment_id, p.state = $state, p.Region = $Region, p.lastupdated = $lastupdated
            WITH p
            MATCH (rt:AWSTransitGatewayRouteTable{TransitGatewayRouteTableId: $route_table_id})
            MERGE (rt)<-[:PROPAGATED_BY]-(p)
            """,
            id=item.get("id"),
            route_table_id=item.get("route_table_id"),
            attachment_id=item.get("attachment_id"),
            state=item.get("state"),
            Region=region,
            lastupdated=update_tag,
        )
