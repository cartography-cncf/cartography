import logging
from dataclasses import dataclass
from typing import Any

import neo4j

from cartography.client.container_registry import AnonymousRegistryClient
from cartography.client.container_registry import RegistryClient
from cartography.client.container_registry import RegistryError
from cartography.client.container_registry import ResolvedRegistryReference
from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.container_image import ContainerImageReference
from cartography.intel.container_image import parse_container_image_reference
from cartography.intel.external_container_images import load_external_container_images
from cartography.intel.railway.utils import is_live_entrypoint
from cartography.intel.railway.utils import preserve_image_relationships
from cartography.intel.railway.utils import unwrap_edges
from cartography.models.railway.serviceinstance import RailwayServiceInstanceSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RailwayExternalImageBinding:
    reference: ContainerImageReference
    resolved_digest: str | None


@dataclass(frozen=True)
class RailwayUnresolvedImageReference:
    source_reference: str
    normalized_reference: str | None


@dataclass(frozen=True)
class RailwayExternalImageState:
    by_instance_id: dict[str, RailwayExternalImageBinding]
    unresolved_by_instance_id: dict[str, RailwayUnresolvedImageReference]


EMPTY_EXTERNAL_IMAGE_STATE = RailwayExternalImageState(
    {},
    {},
)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
    bundles: dict[str, dict[str, Any]],
    tcp_proxies_by_instance: dict[str, list[dict[str, Any]]],
    workspace: dict[str, Any],
    update_tag: int,
    registry_client: RegistryClient | None = None,
) -> RailwayExternalImageState:
    """
    Load the per-environment service instances from the already-fetched project bundles.

    :param tcp_proxies_by_instance: service instance id -> its TCP proxies. Needed to decide
        `is_publicly_exposed`, since tcpProxies is a separate root field rather than part of
        the bundle.
    :param workspace: supplies preferredRegion, the effective region of any instance that
        does not override it.
    """
    external_images, resolved_references = resolve_external_images(
        bundles,
        registry_client,
    )
    load_external_container_images(
        neo4j_session,
        resolved_references,
        update_tag,
    )
    by_project = transform(
        bundles,
        tcp_proxies_by_instance,
        workspace,
        external_images,
    )
    load_service_instances(neo4j_session, by_project, update_tag)
    preserve_unresolved_image_relationships(
        neo4j_session,
        external_images.unresolved_by_instance_id,
        update_tag,
    )
    cleanup(neo4j_session, list(bundles), common_job_parameters)
    return external_images


def resolve_external_images(
    bundles: dict[str, dict[str, Any]],
    registry_client: RegistryClient | None = None,
) -> tuple[RailwayExternalImageState, list[ResolvedRegistryReference]]:
    """Resolve explicit Railway image references once without weakening cleanup safety."""
    if registry_client is None:
        owned_client = AnonymousRegistryClient()
        client: RegistryClient = owned_client
    else:
        owned_client = None
        client = registry_client
    resolved_by_reference: dict[str, ResolvedRegistryReference] = {}
    failed_references: set[str] = set()
    by_instance_id: dict[str, RailwayExternalImageBinding] = {}
    unresolved_by_instance_id: dict[str, RailwayUnresolvedImageReference] = {}

    def mark_unresolved(
        instance: dict[str, Any],
        source_reference: str,
        reference: ContainerImageReference | None,
    ) -> None:
        unresolved = RailwayUnresolvedImageReference(
            source_reference,
            reference.normalized if reference else None,
        )
        unresolved_by_instance_id[instance["id"]] = unresolved

    try:
        for bundle in bundles.values():
            for instance in iter_service_instances(bundle):
                raw_reference = (instance.get("source") or {}).get("image")
                if not raw_reference:
                    continue

                try:
                    reference = parse_container_image_reference(raw_reference)
                except ValueError as error:
                    mark_unresolved(instance, raw_reference, None)
                    logger.warning(
                        "Skipping malformed Railway container image reference on instance %s: %s",
                        instance.get("id"),
                        error,
                    )
                    continue

                by_instance_id[instance["id"]] = RailwayExternalImageBinding(
                    reference,
                    None,
                )
                if reference.normalized not in resolved_by_reference:
                    if reference.normalized in failed_references:
                        mark_unresolved(instance, raw_reference, reference)
                        continue
                    try:
                        resolved_by_reference[reference.normalized] = client.resolve(
                            reference,
                        )
                    except RegistryError as error:
                        failed_references.add(reference.normalized)
                        mark_unresolved(instance, raw_reference, reference)
                        logger.warning(
                            "Could not resolve Railway external image %s: %s",
                            reference.normalized,
                            error,
                        )
                        continue

                resolution = resolved_by_reference[reference.normalized]
                binding = RailwayExternalImageBinding(reference, resolution.top.digest)
                by_instance_id[instance["id"]] = binding
    finally:
        if owned_client is not None:
            owned_client.close()

    return (
        RailwayExternalImageState(
            by_instance_id,
            unresolved_by_instance_id,
        ),
        list(resolved_by_reference.values()),
    )


def iter_service_instances(
    bundle: dict[str, Any],
) -> list[dict[str, Any]]:
    """
    Flatten every service instance across every environment of one project bundle.
    """
    instances = []
    for environment in unwrap_edges(bundle["environments"]):
        instances.extend(unwrap_edges(environment["serviceInstances"]))
    return instances


def _exposure_types(
    instance: dict[str, Any],
    tcp_proxies: list[dict[str, Any]],
) -> list[str]:
    """
    Which kinds of entry point are actually serving traffic right now.

    Merely having a domain or proxy object is not exposure: Railway keeps them around in
    CREATING, DELETING and DELETED states. is_live_entrypoint() also rejects a custom domain
    that has not passed DNS verification, since it does not resolve. This must stay in step
    with the EXPOSE edges, which are gated on the same predicate.

    A TCP proxy is reported separately from the HTTPS domains because it publishes a raw port
    with no TLS termination, which is a materially different exposure.
    """
    domains = instance.get("domains") or {}
    http_entrypoints = [
        *(domains.get("serviceDomains") or []),
        *(domains.get("customDomains") or []),
    ]
    types = []
    if any(is_live_entrypoint(entrypoint) for entrypoint in http_entrypoints):
        types.append("direct")
    if any(is_live_entrypoint(proxy) for proxy in tcp_proxies):
        types.append("tcp_proxy")
    return types


def transform(
    bundles: dict[str, dict[str, Any]],
    tcp_proxies_by_instance: dict[str, list[dict[str, Any]]],
    workspace: dict[str, Any] | None = None,
    external_images: RailwayExternalImageState = EMPTY_EXTERNAL_IMAGE_STATE,
) -> dict[str, list[dict[str, Any]]]:
    # Railway only sets ServiceInstance.region when the instance overrides the workspace
    # default, which is rare, so most instances report null. Falling back to the workspace's
    # preferred region is what actually answers "where does this run", and it is what the
    # ComputeService ontology mapping reads. numReplicas scales an instance within that one
    # region: Railway exposes no per-replica placement, so there is nothing finer to model.
    default_region = (workspace or {}).get("preferredRegion")
    by_project: dict[str, list[dict[str, Any]]] = {}
    for project_id, bundle in bundles.items():
        transformed = []
        for instance in iter_service_instances(bundle):
            source = instance.get("source") or {}
            external_image = external_images.by_instance_id.get(instance["id"])
            reference = external_image.reference if external_image else None
            latest_deployment = instance.get("latestDeployment") or {}
            tcp_proxies = tcp_proxies_by_instance.get(instance["id"], [])
            exposure_types = _exposure_types(instance, tcp_proxies)
            transformed.append(
                {
                    **instance,
                    "source_image": source.get("image"),
                    "source_image_normalized": (
                        reference.normalized if reference else None
                    ),
                    "source_image_registry": reference.registry if reference else None,
                    "source_image_repository": (
                        reference.repository if reference else None
                    ),
                    "source_image_tag": reference.tag if reference else None,
                    "source_image_digest": reference.digest if reference else None,
                    "source_image_reference_type": (
                        ("digest" if reference.digest else "tag") if reference else None
                    ),
                    "resolved_source_image_digest": (
                        external_image.resolved_digest if external_image else None
                    ),
                    "resolved_source_image_reference": (
                        external_image.reference.normalized
                        if external_image and external_image.resolved_digest
                        else None
                    ),
                    "source_repo": source.get("repo"),
                    "latest_deployment_id": latest_deployment.get("id"),
                    "latest_deployment_status": latest_deployment.get("status"),
                    "region": instance.get("region") or default_region,
                    "region_is_workspace_default": not instance.get("region"),
                    "exposed_internet": bool(exposure_types),
                    "exposed_internet_type": exposure_types or None,
                    # DEPRECATED: kept in step with exposed_internet until v1.0.0.
                    "is_publicly_exposed": bool(exposure_types),
                },
            )
        by_project[project_id] = transformed
    return by_project


@timeit
def load_service_instances(
    neo4j_session: neo4j.Session,
    by_project: dict[str, list[dict[str, Any]]],
    update_tag: int,
) -> None:
    for project_id, instances in by_project.items():
        load(
            neo4j_session,
            RailwayServiceInstanceSchema(),
            instances,
            lastupdated=update_tag,
            PROJECT_ID=project_id,
        )


def preserve_unresolved_image_relationships(
    neo4j_session: neo4j.Session,
    unresolved_by_instance_id: dict[str, RailwayUnresolvedImageReference],
    update_tag: int,
) -> None:
    """Keep the last verified edge only for the still-configured reference."""
    if not unresolved_by_instance_id:
        return
    unresolved_images = [
        {
            "source_id": instance_id,
            "source_reference": unresolved.source_reference,
            "normalized_reference": unresolved.normalized_reference,
        }
        for instance_id, unresolved in sorted(unresolved_by_instance_id.items())
    ]
    preserve_image_relationships(
        neo4j_session,
        unresolved_images,
        "RailwayServiceInstance",
        "ExternalContainerImageReference",
        update_tag,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    project_ids: list[str],
    common_job_parameters: dict[str, Any],
) -> None:
    for project_id in project_ids:
        scoped_job_parameters = common_job_parameters.copy()
        scoped_job_parameters["PROJECT_ID"] = project_id
        GraphJob.from_node_schema(
            RailwayServiceInstanceSchema(),
            scoped_job_parameters,
        ).run(neo4j_session)
