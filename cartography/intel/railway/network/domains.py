import logging
from typing import Any

import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.railway.serviceinstances import iter_service_instances
from cartography.intel.railway.utils import is_live_entrypoint
from cartography.models.railway.network.customdomain import RailwayCustomDomainSchema
from cartography.models.railway.network.servicedomain import RailwayServiceDomainSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
    bundles: dict[str, dict[str, Any]],
    update_tag: int,
) -> None:
    """
    Load service domains and custom domains from the already-fetched project bundles.

    Both hang off `serviceInstance.domains` in the same GraphQL sub-tree, so they are synced
    together.
    """
    service_domains, custom_domains = transform(bundles)
    load_service_domains(neo4j_session, service_domains, update_tag)
    load_custom_domains(neo4j_session, custom_domains, update_tag)
    cleanup(neo4j_session, list(bundles), common_job_parameters)


def _exposure_keys(
    entrypoint: dict[str, Any],
    owner: dict[str, Any],
) -> dict[str, Any]:
    """
    The matcher keys for the EXPOSE edge, left null unless the entry point is actually
    serving traffic.

    A null key matches no service instance, so a domain that is still CREATING, on its way
    out, or (for a custom domain) not yet DNS-verified gets no EXPOSE edge. The plain
    service_id / environment_id properties stay on the node either way, so the association
    remains queryable. This mirrors the `is_publicly_exposed` flag, and the two must agree.
    """
    live = is_live_entrypoint(entrypoint)
    return {
        "exposed_service_id": owner["service_id"] if live else None,
        "exposed_environment_id": owner["environment_id"] if live else None,
    }


def transform(
    bundles: dict[str, dict[str, Any]],
) -> tuple[dict[str, list[dict[str, Any]]], dict[str, list[dict[str, Any]]]]:
    """
    Denormalise the owning (service, environment) pair onto each domain and flatten the
    nested custom-domain `status` object.
    """
    service_domains: dict[str, list[dict[str, Any]]] = {}
    custom_domains: dict[str, list[dict[str, Any]]] = {}

    for project_id, bundle in bundles.items():
        project_service_domains: list[dict[str, Any]] = []
        project_custom_domains: list[dict[str, Any]] = []

        for instance in iter_service_instances(bundle):
            owner = {
                "service_id": instance["serviceId"],
                "environment_id": instance["environmentId"],
            }
            domains = instance.get("domains") or {}
            for service_domain in domains.get("serviceDomains") or []:
                project_service_domains.append(
                    {
                        **service_domain,
                        **owner,
                        **_exposure_keys(service_domain, owner),
                    },
                )
            for custom_domain in domains.get("customDomains") or []:
                status = custom_domain.get("status") or {}
                project_custom_domains.append(
                    {
                        **custom_domain,
                        **owner,
                        "verified": bool(status.get("verified")),
                        "certificate_status": status.get("certificateStatus"),
                        "verification_dns_host": status.get("verificationDnsHost"),
                        **_exposure_keys(custom_domain, owner),
                    },
                )

        service_domains[project_id] = project_service_domains
        custom_domains[project_id] = project_custom_domains

    return service_domains, custom_domains


@timeit
def load_service_domains(
    neo4j_session: neo4j.Session,
    by_project: dict[str, list[dict[str, Any]]],
    update_tag: int,
) -> None:
    for project_id, domains in by_project.items():
        load(
            neo4j_session,
            RailwayServiceDomainSchema(),
            domains,
            lastupdated=update_tag,
            PROJECT_ID=project_id,
        )


@timeit
def load_custom_domains(
    neo4j_session: neo4j.Session,
    by_project: dict[str, list[dict[str, Any]]],
    update_tag: int,
) -> None:
    for project_id, domains in by_project.items():
        load(
            neo4j_session,
            RailwayCustomDomainSchema(),
            domains,
            lastupdated=update_tag,
            PROJECT_ID=project_id,
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
            RailwayServiceDomainSchema(),
            scoped_job_parameters,
        ).run(neo4j_session)
        GraphJob.from_node_schema(
            RailwayCustomDomainSchema(),
            scoped_job_parameters,
        ).run(neo4j_session)
