import logging
from typing import Any, Dict, List

import neo4j

from cartography.client.core.tx import load_matchlinks
from cartography.graph.job import GraphJob
from cartography.models.core.common import PropertyRef
from cartography.models.core.relationships import (
    CartographyRelProperties,
    CartographyRelSchema,
    LinkDirection,
    make_source_node_matcher,
    make_target_node_matcher,
    SourceNodeMatcher,
    TargetNodeMatcher,
)
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get(ldap_conn: Any, forest_info: Dict[str, Any]) -> List[Dict[str, Any]]:
    if ldap_conn is None:
        # Minimal placeholder
        return []
    # Trusts can be discovered per domain; here we keep thin and expect callers/tests to mock if needed
    return []


class TrustRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    _sub_resource_label: PropertyRef = PropertyRef("_sub_resource_label", set_in_kwargs=True)
    _sub_resource_id: PropertyRef = PropertyRef("_sub_resource_id", set_in_kwargs=True)
    direction_: PropertyRef = PropertyRef("direction")
    type_: PropertyRef = PropertyRef("type")
    transitive: PropertyRef = PropertyRef("transitive")
    sidfiltering: PropertyRef = PropertyRef("sidfiltering")


class DomainTrustsRel(CartographyRelSchema):
    target_node_label: str = "ADDomain"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher({"id": PropertyRef("target_domain_id")})
    source_node_label: str = "ADDomain"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher({"id": PropertyRef("source_domain_id")})
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "TRUSTS"
    properties: TrustRelProperties = TrustRelProperties()


@timeit
def transform(raw_trusts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    # Expect input with source_domain_id, target_domain_id and props
    return raw_trusts


def load_trusts(
    neo4j_session: neo4j.Session,
    data: List[Dict[str, Any]],
    forest_id: str,
    update_tag: int,
) -> None:
    if not data:
        return
    load_matchlinks(
        neo4j_session,
        DomainTrustsRel(),
        data,
        lastupdated=update_tag,
        _sub_resource_label="ADForest",
        _sub_resource_id=forest_id,
    )


def cleanup(neo4j_session: neo4j.Session, common_job_parameters: Dict[str, Any]) -> None:
    # For matchlinks cleanup
    GraphJob.from_matchlink(
        DomainTrustsRel(),
        "ADForest",
        common_job_parameters["FOREST_ID"],
        common_job_parameters["UPDATE_TAG"],
    ).run(neo4j_session)

