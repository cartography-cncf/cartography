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
from cartography.models.ontology.labels import SECURITY_ISSUE


@dataclass(frozen=True)
class SentraAlertNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="Sentra alert ID.")
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp when this Sentra alert was last seen.",
    )
    name: PropertyRef = PropertyRef(
        "name",
        extra_index=True,
        description="Name of the policy that raised the alert.",
    )
    description: PropertyRef = PropertyRef(
        "description",
        description="Alert description.",
    )
    recommendation: PropertyRef = PropertyRef(
        "recommendation",
        description="Sentra remediation guidance for the alert.",
    )
    severity: PropertyRef = PropertyRef(
        "severity",
        extra_index=True,
        description="Alert severity: `low`, `medium`, `high`, or `critical`.",
    )
    status: PropertyRef = PropertyRef(
        "status",
        extra_index=True,
        description="Alert status: `pending`, `opened`, or `in_progress`.",
    )
    status_reason: PropertyRef = PropertyRef(
        "status_reason",
        description="Reason for the current status, for example `reopened`.",
    )
    alert_type: PropertyRef = PropertyRef(
        "alert_type",
        extra_index=True,
        description="Alert type, for example `VIOLATED_STORE` or `VIOLATED_IAM_ROLE`.",
    )
    risk_type: PropertyRef = PropertyRef(
        "risk_type",
        description="Risk category of the policy, for example `exposed_data` or `excessive_access`.",
    )
    policy_id: PropertyRef = PropertyRef(
        "policy_id",
        extra_index=True,
        description="ID of the Sentra policy that raised the alert.",
    )
    policy_type: PropertyRef = PropertyRef(
        "policy_type",
        description="Type of the Sentra policy that raised the alert.",
    )
    frameworks: PropertyRef = PropertyRef(
        "frameworks",
        description="Compliance frameworks of the policy, for example `GDPR` or `HIPAA`.",
    )
    tags: PropertyRef = PropertyRef(
        "tags",
        description="Tags on the policy that raised the alert.",
    )
    entity_type: PropertyRef = PropertyRef(
        "entity_type",
        extra_index=True,
        description="Type of the violating entity, for example `STORE` or `IAM_ROLE`.",
    )
    entity_id: PropertyRef = PropertyRef(
        "entity_id",
        extra_index=True,
        description="Sentra ID of the violating entity.",
    )
    entity_name: PropertyRef = PropertyRef(
        "entity_name",
        description="Name of the violating entity.",
    )
    entity_cloud_unique_id: PropertyRef = PropertyRef(
        "entity_cloud_unique_id",
        description="Provider-native identifier of the violating entity, as reported by Sentra.",
    )
    connector_id: PropertyRef = PropertyRef(
        "connector_id",
        description="ID of the Sentra connector the alert belongs to.",
    )
    connector_account_id: PropertyRef = PropertyRef(
        "connector_account_id",
        description="Cloud or SaaS account ID of the connector that the alert belongs to.",
    )
    connector_account_type: PropertyRef = PropertyRef(
        "connector_account_type",
        description="Connector account type, for example `AWS`.",
    )
    sensitivity_level: PropertyRef = PropertyRef(
        "sensitivity_level",
        description="Sentra sensitivity level of the violating entity.",
    )
    data_class_ids: PropertyRef = PropertyRef(
        "data_class_ids",
        description="IDs of the Sentra data classes found on the violating entity.",
    )
    occurrences: PropertyRef = PropertyRef(
        "occurrences",
        description="Number of times the alert recurred.",
    )
    total_violated_assets_count: PropertyRef = PropertyRef(
        "total_violated_assets_count",
        description="Number of assets that violate the policy.",
    )
    created_at: PropertyRef = PropertyRef(
        "created_at",
        description="Timestamp when Sentra created the alert.",
    )
    opened_at: PropertyRef = PropertyRef(
        "opened_at",
        description="Timestamp when the alert was opened.",
    )
    last_modified: PropertyRef = PropertyRef(
        "last_modified",
        description="Timestamp when the alert was last modified.",
    )


@dataclass(frozen=True)
class SentraAlertToTenantRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class SentraAlertToTenantRel(CartographyRelSchema):
    """The Sentra organization that raised the alert."""

    target_node_label: str = "SentraTenant"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("TENANT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: SentraAlertToTenantRelProperties = SentraAlertToTenantRelProperties()


@dataclass(frozen=True)
class SentraAlertToEntityRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class SentraAlertToDataStoreRel(CartographyRelSchema):
    """A data store that the alert affects: the store that Sentra raised the alert on, or a store that holds an object that violates the policy."""

    target_node_label: str = "SentraDataStore"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("affected_data_store_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "AFFECTS"
    properties: SentraAlertToEntityRelProperties = SentraAlertToEntityRelProperties()


@dataclass(frozen=True)
class SentraAlertToS3BucketRel(CartographyRelSchema):
    """The S3 bucket that a data store affected by the alert represents, matched on the bucket name."""

    target_node_label: str = "AWSS3Bucket"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("affected_aws_s3_bucket_names", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "AFFECTS"
    properties: SentraAlertToEntityRelProperties = SentraAlertToEntityRelProperties()


@dataclass(frozen=True)
class SentraAlertToRDSInstanceRel(CartographyRelSchema):
    """The RDS DB instance that a data store affected by the alert represents, matched on the instance ARN."""

    target_node_label: str = "AWSRDSInstance"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("affected_aws_rds_instance_arns", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "AFFECTS"
    properties: SentraAlertToEntityRelProperties = SentraAlertToEntityRelProperties()


@dataclass(frozen=True)
class SentraAlertToRDSClusterRel(CartographyRelSchema):
    """The RDS DB cluster that a data store affected by the alert represents, matched on the cluster ARN."""

    target_node_label: str = "AWSRDSCluster"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("affected_aws_rds_cluster_arns", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "AFFECTS"
    properties: SentraAlertToEntityRelProperties = SentraAlertToEntityRelProperties()


@dataclass(frozen=True)
class SentraAlertToDynamoDBTableRel(CartographyRelSchema):
    """The DynamoDB table that a data store affected by the alert represents, matched on the table ARN."""

    target_node_label: str = "AWSDynamoDBTable"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("affected_aws_dynamodb_table_arns", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "AFFECTS"
    properties: SentraAlertToEntityRelProperties = SentraAlertToEntityRelProperties()


@dataclass(frozen=True)
class SentraAlertToRedshiftClusterRel(CartographyRelSchema):
    """The Redshift cluster that a data store affected by the alert represents, matched on the cluster ARN."""

    target_node_label: str = "AWSRedshiftCluster"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("affected_aws_redshift_cluster_arns", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "AFFECTS"
    properties: SentraAlertToEntityRelProperties = SentraAlertToEntityRelProperties()


@dataclass(frozen=True)
class SentraAlertToDataClassRel(CartographyRelSchema):
    """A data class that Sentra found in an object that violates the policy."""

    target_node_label: str = "SentraDataClass"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("violated_data_class_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "INVOLVES"
    properties: SentraAlertToEntityRelProperties = SentraAlertToEntityRelProperties()


@dataclass(frozen=True)
class SentraAlertToPolicyRel(CartographyRelSchema):
    """The policy that raised the alert."""

    target_node_label: str = "SentraPolicy"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("policy_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "GOVERNED_BY"
    properties: SentraAlertToEntityRelProperties = SentraAlertToEntityRelProperties()


@dataclass(frozen=True)
class SentraAlertToAWSRoleRel(CartographyRelSchema):
    """The IAM role that Sentra raised the alert on, matched on the role ARN."""

    target_node_label: str = "AWSRole"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"arn": PropertyRef("affected_aws_role_arn")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "AFFECTS"
    properties: SentraAlertToEntityRelProperties = SentraAlertToEntityRelProperties()


@dataclass(frozen=True)
class SentraAlertSchema(CartographyNodeSchema):
    """
    An active Sentra alert: a policy violation on a data store or identity.

    The Sentra UI calls these issues. Cartography imports alerts whose status is
    `pending`, `opened`, or `in_progress`; cleanup removes alerts that Sentra
    resolved or ignored since the last sync.

    For an alert on a data store, Cartography also reads the objects that violate
    the policy, such as files in a bucket. The alert links with `INVOLVES` to the
    data classes found in those objects, and with `AFFECTS` to the stores that hold
    them. Cartography doesn't create nodes for the objects themselves.

    When an affected data store represents an AWS resource, the alert also links
    with `AFFECTS` directly to that resource, as findings from other security
    tools do. Queries that match `(:SecurityIssue)-[:AFFECTS]->(:ObjectStorage)`
    then include alerts on S3 buckets, and queries that match
    `(:SecurityIssue)-[:AFFECTS]->(:Database)` include alerts on RDS instances,
    DynamoDB tables, and Redshift clusters. An RDS cluster has no `Database`
    label, because its member instances carry it.
    """

    label: str = "SentraAlert"
    properties: SentraAlertNodeProperties = SentraAlertNodeProperties()
    sub_resource_relationship: SentraAlertToTenantRel = SentraAlertToTenantRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            SentraAlertToDataStoreRel(),
            SentraAlertToS3BucketRel(),
            SentraAlertToRDSInstanceRel(),
            SentraAlertToRDSClusterRel(),
            SentraAlertToDynamoDBTableRel(),
            SentraAlertToRedshiftClusterRel(),
            SentraAlertToDataClassRel(),
            SentraAlertToPolicyRel(),
            SentraAlertToAWSRoleRel(),
        ],
    )
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([SECURITY_ISSUE])
