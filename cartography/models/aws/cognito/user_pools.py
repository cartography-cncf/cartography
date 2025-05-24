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
class CognitoUserPoolProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("Id")
    name: PropertyRef = PropertyRef("Name")

    # policies: PropertyRef = PropertyRef("Policies")
    deletion_protection: PropertyRef = PropertyRef("DeletionProtection")
    # lambda_config: PropertyRef = PropertyRef("LambdaConfig")

    last_modified_date: PropertyRef = PropertyRef("LastModifiedDate")
    creation_date: PropertyRef = PropertyRef("CreationDate")

    # schema_attributes: PropertyRef = PropertyRef("SchemaAttributes")
    auto_verified_attributes: PropertyRef = PropertyRef("AutoVerifiedAttributes")
    alias_attributes: PropertyRef = PropertyRef("AliasAttributes")
    # verification_message_template: PropertyRef = PropertyRef(
    #     "VerificationMessageTemplate"
    # )
    # user_attribute_update_settings: PropertyRef = PropertyRef(
    #     "UserAttributeUpdateSettings"
    # )
    mfa_configuration: PropertyRef = PropertyRef("MfaConfiguration")
    estimated_number_of_users: PropertyRef = PropertyRef("EstimatedNumberOfUsers")
    # email_configuration: PropertyRef = PropertyRef("EmailConfiguration")
    # user_pool_tags: PropertyRef = PropertyRef("UserPoolTags")
    domain: PropertyRef = PropertyRef("Domain")
    # admin_create_user_config: PropertyRef = PropertyRef("AdminCreateUserConfig")
    # username_configuration: PropertyRef = PropertyRef("UsernameConfiguration")
    arn: PropertyRef = PropertyRef("Arn")
    # account_recovery_setting: PropertyRef = PropertyRef("AccountRecoverySetting")
    user_pool_tier: PropertyRef = PropertyRef("UserPoolTier")

    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    region: PropertyRef = PropertyRef("Region", set_in_kwargs=True)


@dataclass(frozen=True)
class CognitoUserPoolToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class CognitoUserPoolToAWSAccountRel(CartographyRelSchema):
    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: CognitoUserPoolToAWSAccountRelProperties = (
        CognitoUserPoolToAWSAccountRelProperties()
    )


@dataclass(frozen=True)
class CognitoUserPoolSchema(CartographyNodeSchema):
    label: str = "CognitoUserPool"
    properties: CognitoUserPoolProperties = CognitoUserPoolProperties()
    sub_resource_relationship: CognitoUserPoolToAWSAccountRel = (
        CognitoUserPoolToAWSAccountRel()
    )
