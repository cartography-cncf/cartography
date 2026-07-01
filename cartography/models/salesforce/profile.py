from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class SalesforceProfileNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("Id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("Name", extra_index=True)
    user_type: PropertyRef = PropertyRef("UserType")


@dataclass(frozen=True)
class SalesforceProfileToOrganizationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SalesforceOrganization)-[:RESOURCE]->(:SalesforceProfile)
class SalesforceProfileToOrganizationRel(CartographyRelSchema):
    target_node_label: str = "SalesforceOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ORG_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: SalesforceProfileToOrganizationRelProperties = (
        SalesforceProfileToOrganizationRelProperties()
    )


@dataclass(frozen=True)
class SalesforceProfileSchema(CartographyNodeSchema):
    label: str = "SalesforceProfile"
    properties: SalesforceProfileNodeProperties = SalesforceProfileNodeProperties()
    sub_resource_relationship: SalesforceProfileToOrganizationRel = (
        SalesforceProfileToOrganizationRel()
    )
    # A Profile is a bundle of permissions, so it maps to the PermissionRole ontology.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["PermissionRole"])
