from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class GCPAuditConfigNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="Stable identifier for this IAM audit config entry."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    parent_type: PropertyRef = PropertyRef(
        "parent_type",
        description="Audit config parent type: organization, folder, or project.",
    )
    parent_id: PropertyRef = PropertyRef(
        "parent_id", description="Full resource name of the audit config parent."
    )
    service: PropertyRef = PropertyRef(
        "service",
        extra_index=True,
        description="Service this audit config applies to, such as `allServices` or `cloudtasks.googleapis.com`.",
    )
    has_admin_read: PropertyRef = PropertyRef(
        "has_admin_read",
        description="Whether this audit config includes the `ADMIN_READ` log type.",
    )
    has_data_read: PropertyRef = PropertyRef(
        "has_data_read",
        description="Whether this audit config includes the `DATA_READ` log type.",
    )
    has_data_write: PropertyRef = PropertyRef(
        "has_data_write",
        description="Whether this audit config includes the `DATA_WRITE` log type.",
    )
    audit_log_configs_json: PropertyRef = PropertyRef(
        "audit_log_configs_json",
        description="Raw auditLogConfigs array encoded as JSON, including exemptedMembers when present.",
    )


@dataclass(frozen=True)
class GCPAuditConfigToOrgRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GCPAuditConfigToOrgRel(CartographyRelSchema):
    target_node_label: str = "GCPOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ORG_RESOURCE_NAME", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: GCPAuditConfigToOrgRelProperties = GCPAuditConfigToOrgRelProperties()


@dataclass(frozen=True)
class GCPAuditConfigToFolderRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GCPAuditConfigToFolderRel(CartographyRelSchema):
    target_node_label: str = "GCPFolder"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("FOLDER_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: GCPAuditConfigToFolderRelProperties = (
        GCPAuditConfigToFolderRelProperties()
    )


@dataclass(frozen=True)
class GCPAuditConfigToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GCPAuditConfigToProjectRel(CartographyRelSchema):
    target_node_label: str = "GCPProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("PROJECT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: GCPAuditConfigToProjectRelProperties = (
        GCPAuditConfigToProjectRelProperties()
    )


@dataclass(frozen=True)
class GCPOrgAuditConfigSchema(CartographyNodeSchema):
    """Representation of an organization-scoped GCP IAM audit config entry."""

    label: str = "GCPAuditConfig"
    properties: GCPAuditConfigNodeProperties = GCPAuditConfigNodeProperties()
    sub_resource_relationship: GCPAuditConfigToOrgRel = GCPAuditConfigToOrgRel()


@dataclass(frozen=True)
class GCPFolderAuditConfigSchema(CartographyNodeSchema):
    """Representation of a folder-scoped GCP IAM audit config entry."""

    label: str = "GCPAuditConfig"
    properties: GCPAuditConfigNodeProperties = GCPAuditConfigNodeProperties()
    sub_resource_relationship: GCPAuditConfigToFolderRel = GCPAuditConfigToFolderRel()


@dataclass(frozen=True)
class GCPProjectAuditConfigSchema(CartographyNodeSchema):
    """Representation of a project-scoped GCP IAM audit config entry."""

    label: str = "GCPAuditConfig"
    properties: GCPAuditConfigNodeProperties = GCPAuditConfigNodeProperties()
    sub_resource_relationship: GCPAuditConfigToProjectRel = GCPAuditConfigToProjectRel()
