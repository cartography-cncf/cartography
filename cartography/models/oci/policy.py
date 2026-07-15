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
class OCIPolicyNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="OCI policy OCID.")
    ocid: PropertyRef = PropertyRef(
        "id", extra_index=True, description="OCI policy OCID."
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last update.",
    )
    name: PropertyRef = PropertyRef("name", description="Policy name.")
    description: PropertyRef = PropertyRef(
        "description", description="Policy description."
    )
    compartmentid: PropertyRef = PropertyRef(
        "compartment_id", description="OCID of the compartment containing the policy."
    )
    statements: PropertyRef = PropertyRef(
        "statements", description="Statements written in the OCI policy language."
    )
    createdate: PropertyRef = PropertyRef(
        "time_created", description="Date and time when the policy was created."
    )
    updatedate: PropertyRef = PropertyRef(
        "version_date", description="Date and time when the policy was last updated."
    )


@dataclass(frozen=True)
class OCIPolicyToOCITenancyRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class OCIPolicyToOCITenancyRel(CartographyRelSchema):
    """An OCI tenancy contains a policy as a managed resource."""

    target_node_label: str = "OCITenancy"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"ocid": PropertyRef("OCI_TENANCY_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: OCIPolicyToOCITenancyRelProperties = (
        OCIPolicyToOCITenancyRelProperties()
    )


# DEPRECATED: OCI_POLICY relationship for backward compatibility
@dataclass(frozen=True)
class OCIPolicyToParentRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


# DEPRECATED: OCI_POLICY relationship for backward compatibility (tenancy)
@dataclass(frozen=True)
class OCIPolicyToTenancyParentRel(CartographyRelSchema):
    """Deprecated compatibility edge from an OCI tenancy to a tenancy-level policy."""

    target_node_label: str = "OCITenancy"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"ocid": PropertyRef("compartment_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "OCI_POLICY"
    properties: OCIPolicyToParentRelProperties = OCIPolicyToParentRelProperties()


# OCI_POLICY relationship to parent compartment
@dataclass(frozen=True)
class OCIPolicyToCompartmentParentRel(CartographyRelSchema):
    """Compatibility edge from an OCI compartment to a compartment-level policy."""

    target_node_label: str = "OCICompartment"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"ocid": PropertyRef("compartment_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "OCI_POLICY"
    properties: OCIPolicyToParentRelProperties = OCIPolicyToParentRelProperties()


@dataclass(frozen=True)
class OCIPolicyRefNodeProperties(CartographyNodeProperties):
    """
    Node properties for policy references schema.
    Uses 'ocid' as data source since data comes from Neo4j queries.
    """

    id: PropertyRef = PropertyRef("ocid", description="OCI policy OCID.")
    ocid: PropertyRef = PropertyRef(
        "ocid", extra_index=True, description="OCI policy OCID."
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last update.",
    )
    name: PropertyRef = PropertyRef("name", description="Policy name.")
    compartmentid: PropertyRef = PropertyRef(
        "compartmentid", description="OCID of the compartment containing the policy."
    )
    statements: PropertyRef = PropertyRef(
        "statements", description="Statements written in the OCI policy language."
    )


@dataclass(frozen=True)
class OCIPolicyToGroupRefRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class OCIPolicyToGroupRefRel(CartographyRelSchema):
    """An OCI policy references a group identified in its policy statements."""

    target_node_label: str = "OCIGroup"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"ocid": PropertyRef("referenced_group_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "OCI_POLICY_REFERENCE"
    properties: OCIPolicyToGroupRefRelProperties = OCIPolicyToGroupRefRelProperties()


@dataclass(frozen=True)
class OCIPolicyToCompartmentRefRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class OCIPolicyToCompartmentRefRel(CartographyRelSchema):
    """An OCI policy references a compartment identified in its statements."""

    target_node_label: str = "OCICompartment"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"ocid": PropertyRef("referenced_compartment_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "OCI_POLICY_REFERENCE"
    properties: OCIPolicyToCompartmentRefRelProperties = (
        OCIPolicyToCompartmentRefRelProperties()
    )


@dataclass(frozen=True)
class OCIPolicySchema(CartographyNodeSchema):
    """An OCI policy with the PermissionRole label and compatibility parent edges."""

    label: str = "OCIPolicy"
    properties: OCIPolicyNodeProperties = OCIPolicyNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["PermissionRole"])
    sub_resource_relationship: OCIPolicyToOCITenancyRel = OCIPolicyToOCITenancyRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            OCIPolicyToTenancyParentRel(),  # Deprecated: replaced by RESOURCE
            OCIPolicyToCompartmentParentRel(),  # OCI_POLICY to parent compartment
        ],
    )


@dataclass(frozen=True)
class OCIPolicyWithReferencesSchema(CartographyNodeSchema):
    """An OCI policy with the PermissionRole label and compatibility parent edges."""

    label: str = "OCIPolicy"
    properties: OCIPolicyRefNodeProperties = OCIPolicyRefNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["PermissionRole"])
    sub_resource_relationship: OCIPolicyToOCITenancyRel = OCIPolicyToOCITenancyRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            OCIPolicyToGroupRefRel(),
            OCIPolicyToCompartmentRefRel(),
        ],
    )
