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
class ECRPullThroughCacheRuleNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    registry_id: PropertyRef = PropertyRef("registry_id", extra_index=True)
    ecr_repository_prefix: PropertyRef = PropertyRef(
        "ecr_repository_prefix", extra_index=True
    )
    upstream_registry_url: PropertyRef = PropertyRef("upstream_registry_url")
    upstream_registry: PropertyRef = PropertyRef("upstream_registry", extra_index=True)
    upstream_repository_prefix: PropertyRef = PropertyRef("upstream_repository_prefix")
    credential_arn: PropertyRef = PropertyRef("credential_arn", extra_index=True)
    custom_role_arn: PropertyRef = PropertyRef("custom_role_arn", extra_index=True)
    created_at: PropertyRef = PropertyRef("created_at")
    updated_at: PropertyRef = PropertyRef("updated_at")
    region: PropertyRef = PropertyRef("Region", set_in_kwargs=True)
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ECRPullThroughCacheRuleRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ECRPullThroughCacheRuleToAWSAccountRel(CartographyRelSchema):
    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ECRPullThroughCacheRuleRelProperties = (
        ECRPullThroughCacheRuleRelProperties()
    )


@dataclass(frozen=True)
class ECRPullThroughCacheRuleToSecretsManagerSecretRel(CartographyRelSchema):
    target_node_label: str = "AWSSecretsManagerSecret"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"arn": PropertyRef("credential_arn")}
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "USES_SECRET"
    properties: ECRPullThroughCacheRuleRelProperties = (
        ECRPullThroughCacheRuleRelProperties()
    )


@dataclass(frozen=True)
class ECRPullThroughCacheRuleToAWSRoleRel(CartographyRelSchema):
    target_node_label: str = "AWSRole"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"arn": PropertyRef("custom_role_arn")}
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "ASSOCIATED_WITH"
    properties: ECRPullThroughCacheRuleRelProperties = (
        ECRPullThroughCacheRuleRelProperties()
    )


@dataclass(frozen=True)
class ECRPullThroughCacheRuleSchema(CartographyNodeSchema):
    label: str = "AWSECRPullThroughCacheRule"
    # DEPRECATED: legacy ECRPullThroughCacheRule node label will be removed in v1.0.0.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["ECRPullThroughCacheRule"])
    properties: ECRPullThroughCacheRuleNodeProperties = (
        ECRPullThroughCacheRuleNodeProperties()
    )
    sub_resource_relationship: ECRPullThroughCacheRuleToAWSAccountRel = (
        ECRPullThroughCacheRuleToAWSAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            ECRPullThroughCacheRuleToSecretsManagerSecretRel(),
            ECRPullThroughCacheRuleToAWSRoleRel(),
        ]
    )
