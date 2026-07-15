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
    id: PropertyRef = PropertyRef("Employee_ID", description="Employee ID.")
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last update.",
    )
    employee_id: PropertyRef = PropertyRef(
        "Employee_ID",
        extra_index=True,
        description="Employee ID indexed for lookups.",
    )
    title: PropertyRef = PropertyRef(
        "businessTitle",
        description="Job or business title.",
    )
    name: PropertyRef = PropertyRef("Name", description="Full name.")
    worker_type: PropertyRef = PropertyRef(
        "Worker_Type",
        description="Type of worker, such as employee or contractor.",
    )
    location: PropertyRef = PropertyRef(
        "location",
        description="Office or work location.",
    )
    country: PropertyRef = PropertyRef(
        "country",
        description="Country from the work address.",
    )
    email: PropertyRef = PropertyRef(
        "email",
        extra_index=True,
        description="Work email address indexed for cross-module relationships.",
    )
    cost_center: PropertyRef = PropertyRef(
        "cost_center",
        description="Cost center code.",
    )
    function: PropertyRef = PropertyRef(
        "function",
        description="Functional area.",
    )
    sub_function: PropertyRef = PropertyRef(
        "sub_function",
        description="Sub-functional area.",
    )
    team: PropertyRef = PropertyRef("Team", description="Team name.")
    sub_team: PropertyRef = PropertyRef("Sub_Team", description="Sub-team name.")
    company: PropertyRef = PropertyRef(
        "Company",
        description="Company or legal entity name.",
    )
    source: PropertyRef = PropertyRef(
        "source",
        description='Data source, always "WORKDAY".',
    )


@dataclass(frozen=True)
class WorkdayHumanToOrganizationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class WorkdayHumanToOrganizationRel(CartographyRelSchema):
    """A Workday person is a member of a supervisory organization."""

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
    """A Workday person reports to another Workday person."""

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
    """A person in Workday with the Human label for identity integration."""

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
