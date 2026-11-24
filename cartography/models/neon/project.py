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
from cartography.models.ontology.labels import TENANT


@dataclass(frozen=True)
class NeonProjectNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description="The project id (e.g. `flat-sea-44148707`), used in every project-scoped API path",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name", description="Display name of the project")
    region_id: PropertyRef = PropertyRef(
        "region_id",
        description="The region hosting the project (e.g. `aws-us-east-2`)",
    )
    platform_id: PropertyRef = PropertyRef(
        "platform_id", description="The cloud platform hosting the project"
    )
    pg_version: PropertyRef = PropertyRef(
        "pg_version", description="The major Postgres version of the project"
    )
    proxy_host: PropertyRef = PropertyRef(
        "proxy_host",
        description="The regional proxy host that compute endpoint hostnames hang off",
    )
    org_id: PropertyRef = PropertyRef(
        "org_id", description="Id of the owning organization"
    )
    owner_id: PropertyRef = PropertyRef(
        "owner_id", description="Id of the account that owns the project"
    )
    creation_source: PropertyRef = PropertyRef(
        "creation_source",
        description="How the project was created (`console`, `neonctl`, ...)",
    )
    created_at: PropertyRef = PropertyRef(
        "created_at", description="When the project was created"
    )
    updated_at: PropertyRef = PropertyRef(
        "updated_at", description="When the project was last changed"
    )
    compute_last_active_at: PropertyRef = PropertyRef(
        "compute_last_active_at",
        description="When any compute in the project was last active",
    )
    history_retention_seconds: PropertyRef = PropertyRef(
        "history_retention_seconds",
        description="How far back, in seconds, the restore window reaches",
    )
    store_passwords: PropertyRef = PropertyRef(
        "store_passwords",
        description="Whether Neon stores role passwords so the Console can reveal them",
    )

    # Network posture, rolled up from the project settings. These drive the
    # exposure verdict on every NeonEndpoint in the project.
    allowed_ips: PropertyRef = PropertyRef(
        "allowed_ips",
        description="IP addresses, ranges and CIDRs allowed to connect. An empty or absent value means any address may connect",
    )
    allowed_ips_protected_branches_only: PropertyRef = PropertyRef(
        "allowed_ips_protected_branches_only",
        description="When `True`, the IP allowlist applies to protected branches only and every other branch accepts any address",
    )
    block_public_connections: PropertyRef = PropertyRef(
        "block_public_connections",
        description="Whether connections over the public internet are refused, leaving only private networking",
    )
    block_vpc_connections: PropertyRef = PropertyRef(
        "block_vpc_connections",
        description="Whether connections over VPC endpoints are refused",
    )
    enable_logical_replication: PropertyRef = PropertyRef(
        "enable_logical_replication",
        description="Whether logical replication is enabled, which lets subscribers stream every change out of the database",
    )
    hipaa: PropertyRef = PropertyRef(
        "hipaa", description="Whether the project is HIPAA compliant"
    )
    audit_log_level: PropertyRef = PropertyRef(
        "audit_log_level",
        description="Audit log verbosity for the project (`base`, `extended`, `full`)",
    )


@dataclass(frozen=True)
class NeonProjectToOrganizationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:NeonOrganization)-[:RESOURCE]->(:NeonProject)
class NeonProjectToOrganizationRel(CartographyRelSchema):
    target_node_label: str = "NeonOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ORG_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: NeonProjectToOrganizationRelProperties = (
        NeonProjectToOrganizationRelProperties()
    )


@dataclass(frozen=True)
class NeonProjectSchema(CartographyNodeSchema):
    """Represents a Neon project: the isolation boundary holding branches, compute endpoints, databases, roles and object storage buckets."""

    label: str = "NeonProject"
    properties: NeonProjectNodeProperties = NeonProjectNodeProperties()
    sub_resource_relationship: NeonProjectToOrganizationRel = (
        NeonProjectToOrganizationRel()
    )
    # A project is Neon's isolation boundary and the sub resource for every
    # resource below it, so it carries Tenant alongside SupabaseProject / AWSAccount.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([TENANT])
