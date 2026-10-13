from string import Template

import neo4j

from cartography.client.core.tx import read_list_of_values_tx

_EXISTING_RESOURCE_IDS_TEMPLATE = Template(
    """
    UNWIND $ResourceIds AS resource_id
    MATCH (:AWSAccount{id: $AWS_ID})-[:RESOURCE]->(resource:$label{$property: resource_id})
    $region_filter
    RETURN DISTINCT resource_id
    """,
)


def get_existing_resource_ids(
    neo4j_session: neo4j.Session,
    resource_ids: list[str],
    label: str,
    property: str,
    region_property: str | None,
    region: str,
    aws_account_id: str,
) -> set[str]:
    """
    Return the subset of `resource_ids` that identify a `label` node owned by the account.

    The tagging API reports every tagged resource, including ones whose own sync has
    not loaded them into the graph. Tag nodes are only created for resources that
    exist, so callers filter the tagging data through this first.
    """
    if not resource_ids:
        return set()
    query = _EXISTING_RESOURCE_IDS_TEMPLATE.safe_substitute(
        label=label,
        property=property,
        region_filter=(
            f"WHERE resource.{region_property} = $Region" if region_property else ""
        ),
    )
    return set(
        neo4j_session.execute_read(
            read_list_of_values_tx,
            query,
            ResourceIds=resource_ids,
            AWS_ID=aws_account_id,
            Region=region,
        ),
    )
