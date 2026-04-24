from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class WorkdayHumanNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("Employee_ID")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    employee_id: PropertyRef = PropertyRef("Employee_ID", extra_index=True)
    title: PropertyRef = PropertyRef("businessTitle")
    name: PropertyRef = PropertyRef("Name")
    worker_type: PropertyRef = PropertyRef("Worker_Type")
    location: PropertyRef = PropertyRef("location")
    country: PropertyRef = PropertyRef("country")
    email: PropertyRef = PropertyRef("email", extra_index=True)
    cost_center: PropertyRef = PropertyRef("cost_center")
    function: PropertyRef = PropertyRef("function")
    sub_function: PropertyRef = PropertyRef("sub_function")
    team: PropertyRef = PropertyRef("Team")
    sub_team: PropertyRef = PropertyRef("Sub_Team")
    company: PropertyRef = PropertyRef("Company")
    source: PropertyRef = PropertyRef("source")


@dataclass(frozen=True)
class WorkdayHumanToOrganizationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class WorkdayHumanToOrganizationRel(CartographyRelSchema):
    target_node_label: str = "WorkdayOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("Supervisory_Organization")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "MEMBER_OF_ORGANIZATION"
    properties: WorkdayHumanToOrganizationRelProperties = (
        WorkdayHumanToOrganizationRelProperties()
    )


@dataclass(frozen=True)
class WorkdayHumanToManagerRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class WorkdayHumanToManagerRel(CartographyRelSchema):
    target_node_label: str = "WorkdayHuman"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("Manager_ID")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "REPORTS_TO"
    properties: WorkdayHumanToManagerRelProperties = (
        WorkdayHumanToManagerRelProperties()
    )


@dataclass(frozen=True)
class WorkdayHumanSchema(CartographyNodeSchema):
    label: str = "WorkdayHuman"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["Human"])
    properties: WorkdayHumanNodeProperties = WorkdayHumanNodeProperties()
    other_relationships: OtherRelationships = OtherRelationships(
        rels=[
            WorkdayHumanToOrganizationRel(),
            WorkdayHumanToManagerRel(),
        ],
    )

    @property
    def scoped_cleanup(self) -> bool:
        return False
