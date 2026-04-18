from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import TargetNodeMatcher
from cartography.models.core.relationships import make_target_node_matcher


@dataclass(frozen=True)
class JFrogArtifactoryRepositoryNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", extra_index=True)
    key: PropertyRef = PropertyRef("key")
    description: PropertyRef = PropertyRef("description")
    package_type: PropertyRef = PropertyRef("package_type")
    repo_type: PropertyRef = PropertyRef("repo_type")
    url: PropertyRef = PropertyRef("url")
    project_key: PropertyRef = PropertyRef("project_key")
    rclass: PropertyRef = PropertyRef("rclass")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class JFrogArtifactoryRepositoryToTenantRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:JFrogArtifactoryTenant)-[:RESOURCE]->(:JFrogArtifactoryRepository)
class JFrogArtifactoryRepositoryToTenantRel(CartographyRelSchema):
    target_node_label: str = "JFrogArtifactoryTenant"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("TENANT_ID", set_in_kwargs=True)}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: JFrogArtifactoryRepositoryToTenantRelProperties = (
        JFrogArtifactoryRepositoryToTenantRelProperties()
    )


@dataclass(frozen=True)
class JFrogArtifactoryRepositorySchema(CartographyNodeSchema):
    label: str = "JFrogArtifactoryRepository"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["ContainerRegistry"])
    properties: JFrogArtifactoryRepositoryNodeProperties = (
        JFrogArtifactoryRepositoryNodeProperties()
    )
    sub_resource_relationship: JFrogArtifactoryRepositoryToTenantRel = (
        JFrogArtifactoryRepositoryToTenantRel()
    )
