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
from cartography.models.ontology.labels import COMPUTE_SERVICE
from cartography.models.ontology.labels import CONTAINER
from cartography.models.snowflake.extra_labels import SNOWFLAKE_SECURABLE


@dataclass(frozen=True)
class SnowflakeServiceNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="Account-scoped identifier for the service."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="The service name."
    )
    qualified_name: PropertyRef = PropertyRef(
        "qualified_name",
        extra_index=True,
        description="Fully qualified DATABASE.SCHEMA.NAME of the service.",
    )
    database_name: PropertyRef = PropertyRef(
        "database_name", description="Name of the database containing the service."
    )
    schema_name: PropertyRef = PropertyRef(
        "schema_name", description="Name of the schema containing the service."
    )
    status: PropertyRef = PropertyRef(
        "status",
        description="Service status, for example RUNNING, PENDING, SUSPENDED or FAILED.",
    )
    compute_pool: PropertyRef = PropertyRef(
        "compute_pool", description="Name of the compute pool the service runs on."
    )
    spec_digest: PropertyRef = PropertyRef(
        "spec_digest",
        description="Digest of the service specification, which changes on every redeploy.",
    )
    dns_name: PropertyRef = PropertyRef(
        "dns_name",
        extra_index=True,
        description="Internal DNS name other services in the account reach this one at.",
    )
    current_instances: PropertyRef = PropertyRef(
        "current_instances",
        description="Number of service instances currently running.",
    )
    target_instances: PropertyRef = PropertyRef(
        "target_instances",
        description="Number of service instances Snowflake is converging to.",
    )
    min_instances: PropertyRef = PropertyRef(
        "min_instances",
        description="Minimum number of instances the service keeps running.",
    )
    max_instances: PropertyRef = PropertyRef(
        "max_instances",
        description="Maximum number of instances the service may scale to.",
    )
    auto_resume: PropertyRef = PropertyRef(
        "auto_resume",
        description="Whether the service restarts automatically when its compute pool resumes.",
    )
    is_job: PropertyRef = PropertyRef(
        "is_job",
        description="Whether this is a run-to-completion job service rather than a long-running one.",
    )
    is_upgrading: PropertyRef = PropertyRef(
        "is_upgrading",
        description="Whether the service is mid-upgrade to a new specification.",
    )
    query_warehouse: PropertyRef = PropertyRef(
        "query_warehouse",
        description="Name of the warehouse the service's own SQL queries run on.",
    )
    external_access_integrations: PropertyRef = PropertyRef(
        "external_access_integrations",
        description=(
            "Names of the external access integrations the service's containers may make "
            "outbound calls through."
        ),
    )
    owner: PropertyRef = PropertyRef(
        "owner", description="Name of the role that owns the service."
    )
    comment: PropertyRef = PropertyRef("comment", description="Service comment.")
    created_on: PropertyRef = PropertyRef(
        "created_on", description="When the service was created."
    )


@dataclass(frozen=True)
class SnowflakeServiceToAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SnowflakeAccount)-[:RESOURCE]->(:SnowflakeService)
class SnowflakeServiceToAccountRel(CartographyRelSchema):
    """A Snowflake account contains the service as a resource."""

    target_node_label: str = "SnowflakeAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ACCOUNT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: SnowflakeServiceToAccountRelProperties = (
        SnowflakeServiceToAccountRelProperties()
    )


@dataclass(frozen=True)
class SnowflakeServiceToSchemaRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SnowflakeSchema)-[:CONTAINS]->(:SnowflakeService)
class SnowflakeServiceToSchemaRel(CartographyRelSchema):
    """A Snowflake schema contains the service."""

    target_node_label: str = "SnowflakeSchema"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("parent_schema_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONTAINS"
    properties: SnowflakeServiceToSchemaRelProperties = (
        SnowflakeServiceToSchemaRelProperties()
    )


@dataclass(frozen=True)
class SnowflakeServiceToComputePoolRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SnowflakeService)-[:WORKLOAD_PARENT]->(:SnowflakeComputePool)
class SnowflakeServiceToComputePoolRel(CartographyRelSchema):
    """A Snowflake service's containers are scheduled on this compute pool."""

    target_node_label: str = "SnowflakeComputePool"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("compute_pool_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "WORKLOAD_PARENT"
    properties: SnowflakeServiceToComputePoolRelProperties = (
        SnowflakeServiceToComputePoolRelProperties()
    )


@dataclass(frozen=True)
class SnowflakeServiceToWarehouseRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SnowflakeService)-[:USES_WAREHOUSE]->(:SnowflakeWarehouse)
class SnowflakeServiceToWarehouseRel(CartographyRelSchema):
    """A Snowflake service runs its own SQL queries on this warehouse.

    Distinct from the WORKLOAD_PARENT edge to the compute pool: the pool hosts the
    service's containers, whereas the query warehouse is a data-plane dependency the
    container code calls into. Whitelisted in constraints_whitelist.py for that
    reason.
    """

    target_node_label: str = "SnowflakeWarehouse"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("query_warehouse_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "USES_WAREHOUSE"
    properties: SnowflakeServiceToWarehouseRelProperties = (
        SnowflakeServiceToWarehouseRelProperties()
    )


@dataclass(frozen=True)
class SnowflakeServiceToExternalAccessIntegrationRelProperties(
    CartographyRelProperties
):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SnowflakeService)-[:USES_INTEGRATION]->(:SnowflakeExternalAccessIntegration)
class SnowflakeServiceToExternalAccessIntegrationRel(CartographyRelSchema):
    """A Snowflake service makes outbound network calls through this external access integration."""

    target_node_label: str = "SnowflakeExternalAccessIntegration"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("external_access_integration_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "USES_INTEGRATION"
    properties: SnowflakeServiceToExternalAccessIntegrationRelProperties = (
        SnowflakeServiceToExternalAccessIntegrationRelProperties()
    )


@dataclass(frozen=True)
class SnowflakeServiceSchema(CartographyNodeSchema):
    """Represents a Snowflake service: a containerized workload running on Snowpark Container Services."""

    label: str = "SnowflakeService"
    properties: SnowflakeServiceNodeProperties = SnowflakeServiceNodeProperties()
    # ComputeService: ontology label; a service is a managed containerized workload.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(
        [COMPUTE_SERVICE, SNOWFLAKE_SECURABLE],
    )
    sub_resource_relationship: SnowflakeServiceToAccountRel = (
        SnowflakeServiceToAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            SnowflakeServiceToSchemaRel(),
            SnowflakeServiceToComputePoolRel(),
            SnowflakeServiceToWarehouseRel(),
            SnowflakeServiceToExternalAccessIntegrationRel(),
        ],
    )


@dataclass(frozen=True)
class SnowflakeServiceContainerNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description="Account-scoped identifier for the service container instance.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef(
        "name",
        extra_index=True,
        description="Container name as declared in the service specification.",
    )
    instance_id: PropertyRef = PropertyRef(
        "instance_id",
        description="Index of the service instance this container belongs to.",
    )
    service_name: PropertyRef = PropertyRef(
        "service_name",
        description="Fully qualified name of the service that owns the container.",
    )
    status: PropertyRef = PropertyRef(
        "status",
        description="Container status, for example READY, PENDING or FAILED.",
    )
    image_name: PropertyRef = PropertyRef(
        "image_name",
        extra_index=True,
        description="Image reference the container was started from.",
    )
    untagged_image_path: PropertyRef = PropertyRef(
        "untagged_image_path",
        description=(
            "Image reference with the tag removed, used together with the digest to "
            "resolve the one repository image the container is running."
        ),
    )
    image_digest: PropertyRef = PropertyRef(
        "image_digest",
        extra_index=True,
        description="Digest of the running image, which pins exactly what code is executing.",
    )
    restart_count: PropertyRef = PropertyRef(
        "restart_count", description="Number of times the container has restarted."
    )
    message: PropertyRef = PropertyRef(
        "message", description="Most recent status message reported for the container."
    )
    start_time: PropertyRef = PropertyRef(
        "start_time", description="When the container last started."
    )


@dataclass(frozen=True)
class SnowflakeServiceContainerToAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SnowflakeAccount)-[:RESOURCE]->(:SnowflakeServiceContainer)
class SnowflakeServiceContainerToAccountRel(CartographyRelSchema):
    """A Snowflake account contains the service container as a resource."""

    target_node_label: str = "SnowflakeAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ACCOUNT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: SnowflakeServiceContainerToAccountRelProperties = (
        SnowflakeServiceContainerToAccountRelProperties()
    )


@dataclass(frozen=True)
class SnowflakeServiceContainerToServiceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SnowflakeServiceContainer)-[:WORKLOAD_PARENT]->(:SnowflakeService)
class SnowflakeServiceContainerToServiceRel(CartographyRelSchema):
    """A Snowflake service container runs as part of this service."""

    target_node_label: str = "SnowflakeService"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("parent_service_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "WORKLOAD_PARENT"
    properties: SnowflakeServiceContainerToServiceRelProperties = (
        SnowflakeServiceContainerToServiceRelProperties()
    )


@dataclass(frozen=True)
class SnowflakeServiceContainerToImageRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SnowflakeServiceContainer)-[:HAS_IMAGE]->(:SnowflakeImage)
class SnowflakeServiceContainerToImageRel(CartographyRelSchema):
    """A Snowflake service container runs this image from an account image repository.

    Matched on the untagged registry path as well as the digest. The digest alone
    identifies the image *bytes*, not the image object: the same bytes pushed to two
    repositories are two ``SnowflakeImage`` nodes, and a digest-only matcher would
    attach the container to every one of them. Pairing the path with the digest picks
    the single repository the container actually pulled from, while staying tolerant
    of the container and the repository listing reporting different tags.
    """

    target_node_label: str = "SnowflakeImage"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "untagged_image_path": PropertyRef("untagged_image_path"),
            "digest": PropertyRef("image_digest"),
        },
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_IMAGE"
    properties: SnowflakeServiceContainerToImageRelProperties = (
        SnowflakeServiceContainerToImageRelProperties()
    )


@dataclass(frozen=True)
class SnowflakeServiceContainerSchema(CartographyNodeSchema):
    """Represents one container instance of a Snowflake service."""

    label: str = "SnowflakeServiceContainer"
    properties: SnowflakeServiceContainerNodeProperties = (
        SnowflakeServiceContainerNodeProperties()
    )
    # Container: ontology label; this is a running container instance.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([CONTAINER])
    sub_resource_relationship: SnowflakeServiceContainerToAccountRel = (
        SnowflakeServiceContainerToAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            SnowflakeServiceContainerToServiceRel(),
            SnowflakeServiceContainerToImageRel(),
        ],
    )


@dataclass(frozen=True)
class SnowflakeServiceEndpointNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="Account-scoped identifier for the service endpoint."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef(
        "name",
        extra_index=True,
        description="Endpoint name as declared in the service specification.",
    )
    service_name: PropertyRef = PropertyRef(
        "service_name",
        description="Fully qualified name of the service that exposes the endpoint.",
    )
    port: PropertyRef = PropertyRef(
        "port", description="Container port the endpoint forwards to."
    )
    port_range: PropertyRef = PropertyRef(
        "port_range",
        description="Container port range the endpoint forwards to, if a range.",
    )
    protocol: PropertyRef = PropertyRef(
        "protocol", description="Endpoint protocol, for example HTTP or TCP."
    )
    is_public: PropertyRef = PropertyRef(
        "is_public",
        description=(
            "Whether the endpoint is reachable from the public internet through a "
            "Snowflake-managed ingress rather than only from inside the account."
        ),
    )
    ingress_url: PropertyRef = PropertyRef(
        "ingress_url",
        extra_index=True,
        description="Public ingress URL Snowflake assigned to a public endpoint.",
    )


@dataclass(frozen=True)
class SnowflakeServiceEndpointToAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SnowflakeAccount)-[:RESOURCE]->(:SnowflakeServiceEndpoint)
class SnowflakeServiceEndpointToAccountRel(CartographyRelSchema):
    """A Snowflake account contains the service endpoint as a resource."""

    target_node_label: str = "SnowflakeAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ACCOUNT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: SnowflakeServiceEndpointToAccountRelProperties = (
        SnowflakeServiceEndpointToAccountRelProperties()
    )


@dataclass(frozen=True)
class SnowflakeServiceEndpointToServiceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SnowflakeService)-[:HAS_ENDPOINT]->(:SnowflakeServiceEndpoint)
class SnowflakeServiceEndpointToServiceRel(CartographyRelSchema):
    """A Snowflake service exposes this endpoint."""

    target_node_label: str = "SnowflakeService"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("parent_service_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_ENDPOINT"
    properties: SnowflakeServiceEndpointToServiceRelProperties = (
        SnowflakeServiceEndpointToServiceRelProperties()
    )


@dataclass(frozen=True)
class SnowflakeServiceEndpointSchema(CartographyNodeSchema):
    """Represents a network endpoint exposed by a Snowflake service."""

    label: str = "SnowflakeServiceEndpoint"
    properties: SnowflakeServiceEndpointNodeProperties = (
        SnowflakeServiceEndpointNodeProperties()
    )
    sub_resource_relationship: SnowflakeServiceEndpointToAccountRel = (
        SnowflakeServiceEndpointToAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [SnowflakeServiceEndpointToServiceRel()],
    )


@dataclass(frozen=True)
class SnowflakeServiceRoleNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="Account-scoped identifier for the service role."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="The service role name."
    )
    service_name: PropertyRef = PropertyRef(
        "service_name",
        description="Fully qualified name of the service that declares the role.",
    )
    comment: PropertyRef = PropertyRef("comment", description="Service role comment.")


@dataclass(frozen=True)
class SnowflakeServiceRoleToAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SnowflakeAccount)-[:RESOURCE]->(:SnowflakeServiceRole)
class SnowflakeServiceRoleToAccountRel(CartographyRelSchema):
    """A Snowflake account contains the service role as a resource."""

    target_node_label: str = "SnowflakeAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ACCOUNT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: SnowflakeServiceRoleToAccountRelProperties = (
        SnowflakeServiceRoleToAccountRelProperties()
    )


@dataclass(frozen=True)
class SnowflakeServiceRoleToServiceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SnowflakeService)-[:HAS_SERVICE_ROLE]->(:SnowflakeServiceRole)
class SnowflakeServiceRoleToServiceRel(CartographyRelSchema):
    """A Snowflake service declares this service role, which gates access to its endpoints."""

    target_node_label: str = "SnowflakeService"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("parent_service_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_SERVICE_ROLE"
    properties: SnowflakeServiceRoleToServiceRelProperties = (
        SnowflakeServiceRoleToServiceRelProperties()
    )


@dataclass(frozen=True)
class SnowflakeServiceRoleSchema(CartographyNodeSchema):
    """Represents a service role declared by a Snowflake service to gate endpoint access."""

    label: str = "SnowflakeServiceRole"
    properties: SnowflakeServiceRoleNodeProperties = (
        SnowflakeServiceRoleNodeProperties()
    )
    sub_resource_relationship: SnowflakeServiceRoleToAccountRel = (
        SnowflakeServiceRoleToAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [SnowflakeServiceRoleToServiceRel()],
    )
