# Association/Propagation helpers — not yet implemented

def get_transit_gateway_route_table_associations(boto3_session: boto3.session.Session, region: str) -> list[dict[str, Any]]:
    # TODO: implement describe_transit_gateway_route_table_associations paginator
    return []


def transform_tgw_route_table_associations(data: list[dict[str, Any]]) -> list[dict[str, Any]]:
    # TODO: implement transformation
    return []


def load_transit_gateway_route_table_associations(neo4j_session: neo4j.Session, data: list[dict[str, Any]], region: str, current_aws_account_id: str, update_tag: int) -> None:
    # TODO: implement load using cartography.load or matchlink
    return


def get_transit_gateway_route_table_propagations(boto3_session: boto3.session.Session, region: str) -> list[dict[str, Any]]:
    # TODO: implement describe_transit_gateway_route_table_propagations paginator
    return []


def transform_tgw_route_table_propagations(data: list[dict[str, Any]]) -> list[dict[str, Any]]:
    # TODO: implement transformation
    return []


def load_transit_gateway_route_table_propagations(neo4j_session: neo4j.Session, data: list[dict[str, Any]], region: str, current_aws_account_id: str, update_tag: int) -> None:
    # TODO: implement load using cartography.load or matchlink
    return
