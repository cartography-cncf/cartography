from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class SemgrepSCALocationProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "findingId",
        description="Unique identifier for the vulnerable dependency usage location.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    path: PropertyRef = PropertyRef(
        "path",
        extra_index=True,
        description="Path of the file containing the vulnerable dependency usage.",
    )
    start_line: PropertyRef = PropertyRef(
        "startLine",
        description="Line where the usage starts.",
    )
    start_col: PropertyRef = PropertyRef(
        "startCol",
        description="Column where the usage starts.",
    )
    end_line: PropertyRef = PropertyRef(
        "endLine",
        description="Line where the usage ends.",
    )
    end_col: PropertyRef = PropertyRef(
        "endCol",
        description="Column where the usage ends.",
    )
    url: PropertyRef = PropertyRef(
        "url",
        description="URL of the file containing the usage.",
    )


@dataclass(frozen=True)
class SemgrepSCALocToSemgrepSCAFindingRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SemgrepSCALocation)<-[:USAGE_AT]-(:SemgrepSCAFinding)
class SemgrepSCALocToSemgrepSCAFindingRel(CartographyRelSchema):
    """Links an SCA finding to a source location where the dependency is used."""

    target_node_label: str = "SemgrepSCAFinding"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("SCA_ID")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "USAGE_AT"
    properties: SemgrepSCALocToSemgrepSCAFindingRelProperties = (
        SemgrepSCALocToSemgrepSCAFindingRelProperties()
    )


@dataclass(frozen=True)
class SemgrepSCALocToSemgrepSCADeploymentRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SemgrepSCALocation)<-[:RESOURCE]-(:SemgrepSCADeployment)
class SemgrepSCALocToSCADeploymentRel(CartographyRelSchema):
    """Connects a Semgrep deployment to one of its SCA usage locations."""

    target_node_label: str = "SemgrepDeployment"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("DEPLOYMENT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: SemgrepSCALocToSemgrepSCADeploymentRelProperties = (
        SemgrepSCALocToSemgrepSCADeploymentRelProperties()
    )


@dataclass(frozen=True)
class SemgrepSCALocationSchema(CartographyNodeSchema):
    """A source location where vulnerable dependency code is used."""

    label: str = "SemgrepSCALocation"
    properties: SemgrepSCALocationProperties = SemgrepSCALocationProperties()
    sub_resource_relationship: SemgrepSCALocToSCADeploymentRel = (
        SemgrepSCALocToSCADeploymentRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            SemgrepSCALocToSemgrepSCAFindingRel(),
        ],
    )
