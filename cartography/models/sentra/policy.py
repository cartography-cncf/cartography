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
class SentraPolicyNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="Sentra policy ID.")
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp when this Sentra policy was last seen.",
    )
    name: PropertyRef = PropertyRef(
        "name",
        extra_index=True,
        description="Policy name.",
    )
    description: PropertyRef = PropertyRef(
        "description",
        description="What the policy detects and the impact of a violation.",
    )
    canonical: PropertyRef = PropertyRef(
        "canonical",
        extra_index=True,
        description="Stable identifier of the policy across revisions, for example `public-s3-bucket`.",
    )
    revision: PropertyRef = PropertyRef(
        "revision",
        description="Policy revision.",
    )
    severity: PropertyRef = PropertyRef(
        "severity",
        extra_index=True,
        description="Severity of the alerts that the policy raises: `info`, `low`, `medium`, `high`, `critical`, or `none`.",
    )
    status: PropertyRef = PropertyRef(
        "status",
        extra_index=True,
        description="Policy status: `enabled` or `disabled`.",
    )
    policy_type: PropertyRef = PropertyRef(
        "policy_type",
        description="Policy type, for example `rule_based`, `sql_based`, or `threat_detection`.",
    )
    risk_type: PropertyRef = PropertyRef(
        "risk_type",
        extra_index=True,
        description="Risk category that the policy detects, for example `exposed_data` or `excessive_access`.",
    )
    alert_type: PropertyRef = PropertyRef(
        "alert_type",
        description="Kind of entity that the policy raises alerts on, for example `store`, `asset`, or `iam_role`.",
    )
    entity_type: PropertyRef = PropertyRef(
        "entity_type",
        description="Kind of entity that the policy evaluates: `store` or `asset`.",
    )
    triggering_type: PropertyRef = PropertyRef(
        "triggering_type",
        description="How the policy runs: `automatic` or `manual`.",
    )
    predefined: PropertyRef = PropertyRef(
        "predefined",
        description="Whether the policy is built into Sentra rather than written by your organization.",
    )
    frameworks: PropertyRef = PropertyRef(
        "frameworks",
        description="Compliance frameworks that the policy maps to, for example `GDPR` or `PCI`.",
    )
    tags: PropertyRef = PropertyRef(
        "tags",
        description="Tags on the policy.",
    )
    recommendation: PropertyRef = PropertyRef(
        "recommendation",
        description="Remediation guidance for a violation of the policy.",
    )
    remediation_actions: PropertyRef = PropertyRef(
        "remediation_actions",
        description="Remediation actions that Sentra can take for a violation.",
    )
    auto_approval: PropertyRef = PropertyRef(
        "auto_approval",
        description="Whether Sentra runs the remediation actions without approval.",
    )
    affected_data_classes: PropertyRef = PropertyRef(
        "affected_data_classes",
        description="Names of the data classes that the policy rules check for.",
    )
    affected_data_class_categories: PropertyRef = PropertyRef(
        "affected_data_class_categories",
        description="Data class categories that the policy rules check for, when the rules name categories instead of data classes.",
    )
    opened_alerts: PropertyRef = PropertyRef(
        "opened_alerts",
        description="Number of open alerts that the policy raised.",
    )
    created_at: PropertyRef = PropertyRef(
        "created_at",
        description="Timestamp when the policy was created.",
    )


@dataclass(frozen=True)
class SentraPolicyToTenantRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class SentraPolicyToTenantRel(CartographyRelSchema):
    """The Sentra organization that the policy belongs to."""

    target_node_label: str = "SentraTenant"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("TENANT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: SentraPolicyToTenantRelProperties = SentraPolicyToTenantRelProperties()


@dataclass(frozen=True)
class SentraPolicyToDataClassRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class SentraPolicyToDataClassRel(CartographyRelSchema):
    """A data class that the policy rules check for, matched on the class name or on its category."""

    target_node_label: str = "SentraDataClass"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("classification_data_class_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "CLASSIFICATION"
    properties: SentraPolicyToDataClassRelProperties = (
        SentraPolicyToDataClassRelProperties()
    )


@dataclass(frozen=True)
class SentraPolicySchema(CartographyNodeSchema):
    """
    A Sentra policy: a rule that raises an alert when a data store or identity violates it.

    The node holds the context of a violation: the compliance frameworks that the
    policy maps to, the risk that it detects, and how to remediate it. Cartography
    imports both enabled and disabled policies. Each alert links to the policy that
    raised it with `GOVERNED_BY`, and the policy links with `CLASSIFICATION` to the
    data classes that its rules check for.
    """

    label: str = "SentraPolicy"
    properties: SentraPolicyNodeProperties = SentraPolicyNodeProperties()
    sub_resource_relationship: SentraPolicyToTenantRel = SentraPolicyToTenantRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [SentraPolicyToDataClassRel()],
    )
