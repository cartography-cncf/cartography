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
from cartography.models.ontology.labels import COMPUTE_INSTANCE


@dataclass(frozen=True)
class RenderServiceNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="ID of the Render service.")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="Name of the service."
    )
    owner_id: PropertyRef = PropertyRef(
        "ownerId", description="ID of the owning Render workspace."
    )
    environment_id: PropertyRef = PropertyRef(
        "environmentId",
        extra_index=True,
        description="ID of the environment this service is deployed in.",
    )
    type: PropertyRef = PropertyRef(
        "type",
        description=(
            "Service type: `web_service`, `private_service`, `background_worker`, "
            "`cron_job`, or `static_site`."
        ),
    )
    slug: PropertyRef = PropertyRef("slug", description="URL-friendly service slug.")
    repo: PropertyRef = PropertyRef(
        "repo", description="Source code repository URL, if deployed from git."
    )
    branch: PropertyRef = PropertyRef(
        "branch", description="Git branch that triggers deploys."
    )
    root_dir: PropertyRef = PropertyRef(
        "rootDir", description="Repository subdirectory built by the service."
    )
    dashboard_url: PropertyRef = PropertyRef(
        "dashboardUrl", description="URL of the service in the Render dashboard."
    )
    suspended: PropertyRef = PropertyRef(
        "suspended", description="Whether the service is suspended."
    )
    auto_deploy: PropertyRef = PropertyRef(
        "autoDeploy", description="Whether the service automatically deploys on push."
    )
    runtime: PropertyRef = PropertyRef(
        "runtime", description="Runtime environment (e.g. `docker`, `node`, `python`)."
    )
    plan: PropertyRef = PropertyRef("plan", description="Instance plan/size.")
    region: PropertyRef = PropertyRef("region", description="Deployment region.")
    url: PropertyRef = PropertyRef(
        "url", extra_index=True, description="Public URL of the service, if any."
    )
    num_instances: PropertyRef = PropertyRef(
        "numInstances", description="Number of running instances."
    )
    registry_credential_id: PropertyRef = PropertyRef(
        "registryCredentialId",
        extra_index=True,
        description="ID of the registry credential used to pull this service's image, if any.",
    )
    created_at: PropertyRef = PropertyRef(
        "createdAt", description="Time when the service was created."
    )
    updated_at: PropertyRef = PropertyRef(
        "updatedAt", description="Time when the service was last modified."
    )
    # Latest deploy only, not full deploy history: Render's deploy history is
    # unbounded and time-series in nature (a poor fit for a current-state graph),
    # so only "what's live right now" is captured, mirroring how RailwayServiceInstance
    # carries latest_deployment_id/latest_deployment_status instead of a node per deploy.
    latest_deploy_id: PropertyRef = PropertyRef(
        "latestDeployId", description="ID of the most recent deploy."
    )
    latest_deploy_status: PropertyRef = PropertyRef(
        "latestDeployStatus", description="Status of the most recent deploy."
    )
    latest_deploy_trigger: PropertyRef = PropertyRef(
        "latestDeployTrigger", description="What triggered the most recent deploy."
    )
    latest_deploy_created_at: PropertyRef = PropertyRef(
        "latestDeployCreatedAt", description="When the most recent deploy was created."
    )
    latest_deploy_finished_at: PropertyRef = PropertyRef(
        "latestDeployFinishedAt", description="When the most recent deploy finished."
    )
    latest_deploy_commit_message: PropertyRef = PropertyRef(
        "latestDeployCommitMessage",
        description="Commit message for the most recent deploy, if deployed from git.",
    )
    latest_deploy_image_ref: PropertyRef = PropertyRef(
        "latestDeployImageRef",
        description="Image reference for the most recent deploy, if deployed from an image.",
    )


@dataclass(frozen=True)
class RenderServiceToTenantRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:RenderTenant)-[:RESOURCE]->(:RenderService)
class RenderServiceToTenantRel(CartographyRelSchema):
    """Connects a Render workspace to a service that it contains."""

    target_node_label: str = "RenderTenant"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("OWNER_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: RenderServiceToTenantRelProperties = (
        RenderServiceToTenantRelProperties()
    )


@dataclass(frozen=True)
class RenderServiceToEnvironmentRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:RenderEnvironment)-[:CONTAINS]->(:RenderService)
class RenderServiceToEnvironmentRel(CartographyRelSchema):
    """Connects a Render environment to a service deployed within it."""

    target_node_label: str = "RenderEnvironment"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("environmentId")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONTAINS"
    properties: RenderServiceToEnvironmentRelProperties = (
        RenderServiceToEnvironmentRelProperties()
    )


@dataclass(frozen=True)
class RenderServiceToRegistryCredentialRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:RenderService)-[:USES_CREDENTIAL]->(:RenderRegistryCredential)
class RenderServiceToRegistryCredentialRel(CartographyRelSchema):
    """Connects a service to the registry credential used to pull its image, if any."""

    target_node_label: str = "RenderRegistryCredential"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("registryCredentialId")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "USES_CREDENTIAL"
    properties: RenderServiceToRegistryCredentialRelProperties = (
        RenderServiceToRegistryCredentialRelProperties()
    )


@dataclass(frozen=True)
class RenderServiceSchema(CartographyNodeSchema):
    """A Render service (web service, background worker, cron job, private service, or static site)."""

    label: str = "RenderService"
    properties: RenderServiceNodeProperties = RenderServiceNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([COMPUTE_INSTANCE])
    sub_resource_relationship: RenderServiceToTenantRel = RenderServiceToTenantRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [RenderServiceToEnvironmentRel(), RenderServiceToRegistryCredentialRel()],
    )
