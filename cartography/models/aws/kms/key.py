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
class KMSKeyNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("KeyId")
    arn: PropertyRef = PropertyRef("Arn", extra_index=True)
    creationdate: PropertyRef = PropertyRef("CreationDate")
    deletiondate: PropertyRef = PropertyRef("DeletionDate")
    validto: PropertyRef = PropertyRef("ValidTo")
    enabled: PropertyRef = PropertyRef("Enabled")
    keystate: PropertyRef = PropertyRef("KeyState")
    customkeystoreid: PropertyRef = PropertyRef("CustomKeyStoreId")
    cloudhsmclusterid: PropertyRef = PropertyRef("CloudHsmClusterId")
    region: PropertyRef = PropertyRef("Region", set_in_kwargs=True)
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class KMSKeyToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class KMSKeyToAWSAccountRel(CartographyRelSchema):
    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: KMSKeyToAWSAccountRelProperties = KMSKeyToAWSAccountRelProperties()


@dataclass(frozen=True)
class KMSKeySchema(CartographyNodeSchema):
    label: str = "KMSKey"
    properties: KMSKeyNodeProperties = KMSKeyNodeProperties()
    sub_resource_relationship: KMSKeyToAWSAccountRel = KMSKeyToAWSAccountRel()
