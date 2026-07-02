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
class DatabricksStorageCredentialNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    credential_id: PropertyRef = PropertyRef("credential_id", extra_index=True)
    name: PropertyRef = PropertyRef("name", extra_index=True)
    metastore_id: PropertyRef = PropertyRef("metastore_id", extra_index=True)
    credential_type: PropertyRef = PropertyRef("credential_type")
    owner: PropertyRef = PropertyRef("owner", extra_index=True)
    read_only: PropertyRef = PropertyRef("read_only")
    used_for_managed_storage: PropertyRef = PropertyRef("used_for_managed_storage")
    isolation_mode: PropertyRef = PropertyRef("isolation_mode")
    comment: PropertyRef = PropertyRef("comment")
    aws_iam_role_arn: PropertyRef = PropertyRef("aws_iam_role_arn", extra_index=True)
    azure_managed_identity_id: PropertyRef = PropertyRef(
        "azure_managed_identity_id", extra_index=True
    )
    azure_access_connector_id: PropertyRef = PropertyRef(
        "azure_access_connector_id", extra_index=True
    )
    gcp_service_account_email: PropertyRef = PropertyRef(
        "gcp_service_account_email", extra_index=True
    )
    created_at: PropertyRef = PropertyRef("created_at")
    updated_at: PropertyRef = PropertyRef("updated_at")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DatabricksStorageCredentialToWorkspaceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DatabricksWorkspace)-[:RESOURCE]->(:DatabricksStorageCredential)
class DatabricksStorageCredentialToWorkspaceRel(CartographyRelSchema):
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
    label: str = "DatabricksStorageCredential"
    properties: DatabricksStorageCredentialNodeProperties = (
        DatabricksStorageCredentialNodeProperties()
    )
    # Storage credentials are grantable UC securables.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["DatabricksSecurable"])
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
