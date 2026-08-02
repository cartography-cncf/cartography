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
from cartography.models.databricks.extra_labels import DATABRICKS_SECURABLE


@dataclass(frozen=True)
class DatabricksStorageCredentialNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="Identifier for the storage credential."
    )
    credential_id: PropertyRef = PropertyRef(
        "credential_id",
        extra_index=True,
        description="Databricks identifier for the storage credential.",
    )
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="Name of the storage credential."
    )
    metastore_id: PropertyRef = PropertyRef(
        "metastore_id",
        extra_index=True,
        description="Identifier of the metastore that contains the storage credential.",
    )
    credential_type: PropertyRef = PropertyRef(
        "credential_type", description="Cloud authentication type of the credential."
    )
    owner: PropertyRef = PropertyRef(
        "owner",
        extra_index=True,
        description="Principal that owns the storage credential.",
    )
    read_only: PropertyRef = PropertyRef(
        "read_only", description="Whether the credential permits only read operations."
    )
    used_for_managed_storage: PropertyRef = PropertyRef(
        "used_for_managed_storage",
        description="Whether the credential is restricted to managed storage.",
    )
    isolation_mode: PropertyRef = PropertyRef(
        "isolation_mode",
        description="Workspace isolation mode of the storage credential.",
    )
    comment: PropertyRef = PropertyRef(
        "comment", description="User-provided description of the storage credential."
    )
    aws_iam_role_arn: PropertyRef = PropertyRef(
        "aws_iam_role_arn",
        extra_index=True,
        description="ARN of the AWS IAM role used by the credential.",
    )
    azure_managed_identity_id: PropertyRef = PropertyRef(
        "azure_managed_identity_id",
        extra_index=True,
        description="Identifier of the Azure managed identity used by the credential.",
    )
    azure_access_connector_id: PropertyRef = PropertyRef(
        "azure_access_connector_id",
        extra_index=True,
        description="Resource identifier of the Azure access connector.",
    )
    gcp_service_account_email: PropertyRef = PropertyRef(
        "gcp_service_account_email",
        extra_index=True,
        description="Email address of the Google Cloud service account.",
    )
    created_at: PropertyRef = PropertyRef(
        "created_at", description="Timestamp when the storage credential was created."
    )
    updated_at: PropertyRef = PropertyRef(
        "updated_at",
        description="Timestamp when the storage credential was last updated.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DatabricksStorageCredentialToWorkspaceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DatabricksWorkspace)-[:RESOURCE]->(:DatabricksStorageCredential)
class DatabricksStorageCredentialToWorkspaceRel(CartographyRelSchema):
    """A Databricks storage credential is a resource within a workspace."""

    target_node_label: str = "DatabricksWorkspace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("WORKSPACE_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: DatabricksStorageCredentialToWorkspaceRelProperties = (
        DatabricksStorageCredentialToWorkspaceRelProperties()
    )


@dataclass(frozen=True)
class DatabricksStorageCredentialToMetastoreRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DatabricksMetastore)-[:CONTAINS]->(:DatabricksStorageCredential)
class DatabricksStorageCredentialToMetastoreRel(CartographyRelSchema):
    """A Databricks metastore contains a storage credential."""

    target_node_label: str = "DatabricksMetastore"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("metastore_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONTAINS"
    properties: DatabricksStorageCredentialToMetastoreRelProperties = (
        DatabricksStorageCredentialToMetastoreRelProperties()
    )


@dataclass(frozen=True)
class DatabricksStorageCredentialToAWSPrincipalRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DatabricksStorageCredential)-[:ASSUMES_ROLE]->(:AWSPrincipal)
class DatabricksStorageCredentialToAWSPrincipalRel(CartographyRelSchema):
    """A Databricks storage credential assumes an AWS IAM role."""

    target_node_label: str = "AWSPrincipal"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"arn": PropertyRef("aws_iam_role_arn")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "ASSUMES_ROLE"
    properties: DatabricksStorageCredentialToAWSPrincipalRelProperties = (
        DatabricksStorageCredentialToAWSPrincipalRelProperties()
    )


@dataclass(frozen=True)
class DatabricksStorageCredentialToGCPSARelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DatabricksStorageCredential)-[:IMPERSONATES]->(:GCPServiceAccount)
class DatabricksStorageCredentialToGCPSARel(CartographyRelSchema):
    """A Databricks storage credential impersonates a Google Cloud service account."""

    target_node_label: str = "GCPServiceAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"email": PropertyRef("gcp_service_account_email")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "IMPERSONATES"
    properties: DatabricksStorageCredentialToGCPSARelProperties = (
        DatabricksStorageCredentialToGCPSARelProperties()
    )


@dataclass(frozen=True)
class DatabricksStorageCredentialSchema(CartographyNodeSchema):
    """A Unity Catalog credential for authenticating to cloud storage."""

    label: str = "DatabricksStorageCredential"
    properties: DatabricksStorageCredentialNodeProperties = (
        DatabricksStorageCredentialNodeProperties()
    )
    # Storage credentials are grantable UC securables.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([DATABRICKS_SECURABLE])
    sub_resource_relationship: DatabricksStorageCredentialToWorkspaceRel = (
        DatabricksStorageCredentialToWorkspaceRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            DatabricksStorageCredentialToMetastoreRel(),
            DatabricksStorageCredentialToAWSPrincipalRel(),
            DatabricksStorageCredentialToGCPSARel(),
        ],
    )
