import logging
from typing import Any
from typing import Dict
from typing import List

import neo4j
from googleapiclient.discovery import Resource
from googleapiclient.errors import HttpError

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.gcp.util import gcp_api_execute_with_retry
from cartography.models.gcp.workload_identity import GCPWorkloadIdentityPoolSchema
from cartography.models.gcp.workload_identity import GCPWorkloadIdentityProviderSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get_workload_identity_pools(
    iam_client: Resource, project_id: str
) -> List[Dict[str, Any]]:
    """
    Retrieve all Workload Identity Federation pools for a given project.

    See https://cloud.google.com/iam/docs/reference/rest/v1/projects.locations.workloadIdentityPools/list.
    """
    pools: List[Dict[str, Any]] = []
    parent = f"projects/{project_id}/locations/global"
    request = (
        iam_client.projects().locations().workloadIdentityPools().list(parent=parent)
    )
    while request is not None:
        response = gcp_api_execute_with_retry(request)
        pools.extend(response.get("workloadIdentityPools", []))
        request = (
            iam_client.projects()
            .locations()
            .workloadIdentityPools()
            .list_next(previous_request=request, previous_response=response)
        )
    return pools


@timeit
def get_workload_identity_providers(
    iam_client: Resource, pool_name: str
) -> List[Dict[str, Any]]:
    """
    Retrieve all providers attached to a single Workload Identity Federation pool.

    See https://cloud.google.com/iam/docs/reference/rest/v1/projects.locations.workloadIdentityPools.providers/list.
    """
    providers: List[Dict[str, Any]] = []
    request = (
        iam_client.projects()
        .locations()
        .workloadIdentityPools()
        .providers()
        .list(parent=pool_name)
    )
    while request is not None:
        response = gcp_api_execute_with_retry(request)
        providers.extend(response.get("workloadIdentityPoolProviders", []))
        request = (
            iam_client.projects()
            .locations()
            .workloadIdentityPools()
            .providers()
            .list_next(previous_request=request, previous_response=response)
        )
    return providers


def transform_pools(
    raw_pools: List[Dict[str, Any]],
    project_id: str,
) -> List[Dict[str, Any]]:
    """
    Flatten pool payloads into loader-friendly dicts. The pool's ``name`` field
    (e.g. ``projects/123/locations/global/workloadIdentityPools/my-pool``) is
    used as the node ``id`` so it matches the form embedded in
    ``principal[Set]://`` URIs on policy bindings.
    """
    result: List[Dict[str, Any]] = []
    for pool in raw_pools:
        pool_name = pool.get("name")
        if not pool_name:
            logger.warning(
                "Skipping WIF pool with no 'name' field (state=%s)",
                pool.get("state"),
            )
            continue
        result.append(
            {
                "id": pool_name,
                "name": pool_name,
                "displayName": pool.get("displayName"),
                "description": pool.get("description"),
                "state": pool.get("state"),
                "disabled": pool.get("disabled", False),
                "mode": pool.get("mode"),
                "sessionDuration": pool.get("sessionDuration"),
                "projectId": project_id,
            },
        )
    return result


# GKE-managed pools (`*.svc.id.goog`) are surfaced by the API with
# ``mode == "SYSTEM_TRUST_DOMAIN"``. They cannot list user-defined providers,
# and ``providers.list`` returns a deterministic 400 INVALID_ARGUMENT. We
# treat them as having no listable providers rather than as a failed sync.
_SYSTEM_TRUST_DOMAIN_MODE = "SYSTEM_TRUST_DOMAIN"


def _detect_protocol(provider: Dict[str, Any]) -> str | None:
    if "oidc" in provider:
        return "OIDC"
    if "aws" in provider:
        return "AWS"
    if "saml" in provider:
        return "SAML"
    if "x509" in provider:
        return "X509"
    return None


def transform_providers(
    raw_providers: List[Dict[str, Any]],
    pool: Dict[str, Any],
    project_id: str,
) -> List[Dict[str, Any]]:
    """
    Flatten provider payloads into loader-friendly dicts. A provider is one of
    OIDC, AWS, or SAML; only the populated sub-object is read for protocol
    fields and a ``protocol`` string is set so downstream queries do not need
    to introspect three optional sub-objects.

    The parent ``pool`` is passed in (not just its name) because the
    effective ``enabled`` flag depends on the pool's own state: per GCP, a
    disabled pool cannot exchange or use tokens, so providers under it must
    be reported as not enabled even if the provider itself is ACTIVE.
    """
    pool_name = pool.get("name", "")
    pool_state = pool.get("state")
    pool_disabled = pool.get("disabled", False)
    pool_active = pool_state == "ACTIVE" and not pool_disabled
    result: List[Dict[str, Any]] = []
    for provider in raw_providers:
        provider_name = provider.get("name")
        if not provider_name:
            logger.warning(
                "Skipping WIF provider with no 'name' field under pool %s",
                pool_name,
            )
            continue
        oidc = provider.get("oidc") or {}
        aws = provider.get("aws") or {}
        saml = provider.get("saml") or {}
        state = provider.get("state")
        disabled = provider.get("disabled", False)
        # ``enabled`` is the effective flag used for cross-provider
        # IdentityProvider queries: a provider is only effectively enabled
        # when both the provider AND its pool are ACTIVE and not disabled.
        # A disabled pool blocks federation regardless of provider state.
        enabled = state == "ACTIVE" and not disabled and pool_active
        result.append(
            {
                "id": provider_name,
                "name": provider_name,
                "displayName": provider.get("displayName"),
                "description": provider.get("description"),
                "state": state,
                "disabled": disabled,
                "enabled": enabled,
                "protocol": _detect_protocol(provider),
                "attributeCondition": provider.get("attributeCondition"),
                "oidcIssuerUri": oidc.get("issuerUri"),
                "oidcAllowedAudiences": oidc.get("allowedAudiences"),
                "awsAccountId": aws.get("accountId"),
                "samlIdpMetadataXml": saml.get("idpMetadataXml"),
                "poolName": pool_name,
                "projectId": project_id,
            },
        )
    return result


@timeit
def load_pools(
    neo4j_session: neo4j.Session,
    pools: List[Dict[str, Any]],
    project_id: str,
    gcp_update_tag: int,
) -> None:
    if not pools:
        return
    logger.debug(f"Loading {len(pools)} WIF pools for project {project_id}")
    load(
        neo4j_session,
        GCPWorkloadIdentityPoolSchema(),
        pools,
        lastupdated=gcp_update_tag,
        projectId=project_id,
    )


@timeit
def load_providers(
    neo4j_session: neo4j.Session,
    providers: List[Dict[str, Any]],
    project_id: str,
    gcp_update_tag: int,
) -> None:
    if not providers:
        return
    logger.debug(f"Loading {len(providers)} WIF providers for project {project_id}")
    load(
        neo4j_session,
        GCPWorkloadIdentityProviderSchema(),
        providers,
        lastupdated=gcp_update_tag,
        projectId=project_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: Dict[str, Any],
    providers_sync_complete: bool = True,
) -> None:
    """
    Clean up WIF providers first (children) then pools to avoid orphan
    MEMBER_OF edges.

    When ``providers_sync_complete`` is False (because listing providers
    failed for at least one pool), provider cleanup is skipped: the cleanup
    job would otherwise delete providers we did not re-ingest this run.
    Pool cleanup remains safe because the pool list call is gated on success
    upstream.
    """
    job_params = {
        **common_job_parameters,
        "projectId": common_job_parameters.get("PROJECT_ID"),
    }
    if providers_sync_complete:
        GraphJob.from_node_schema(GCPWorkloadIdentityProviderSchema(), job_params).run(
            neo4j_session
        )
    else:
        logger.warning(
            "Skipping GCPWorkloadIdentityProvider cleanup for project %s: "
            "at least one pool failed to enumerate providers and stale "
            "providers cannot be safely identified.",
            common_job_parameters.get("PROJECT_ID"),
        )
    GraphJob.from_node_schema(GCPWorkloadIdentityPoolSchema(), job_params).run(
        neo4j_session
    )


@timeit
def sync(
    neo4j_session: neo4j.Session,
    iam_client: Resource,
    project_id: str,
    gcp_update_tag: int,
    common_job_parameters: Dict[str, Any],
) -> None:
    """
    Sync Workload Identity Federation pools and their providers for a project.

    The pools and providers endpoints require ``iam.workloadIdentityPools.list``;
    if the caller lacks the permission the API returns 403. We log and skip in
    that case so a missing-permission scenario does not break the broader IAM
    sync.
    """
    logger.info(f"Syncing GCP Workload Identity Federation for project {project_id}")
    try:
        raw_pools = get_workload_identity_pools(iam_client, project_id)
    except HttpError as e:
        if e.resp.status == 403:
            logger.warning(
                "Permission denied listing Workload Identity pools in project %s. "
                "Skipping WIF sync.",
                project_id,
            )
            return
        raise

    logger.info(
        f"Found {len(raw_pools)} Workload Identity pools in project {project_id}"
    )
    pools = transform_pools(raw_pools, project_id)
    load_pools(neo4j_session, pools, project_id, gcp_update_tag)

    all_providers: List[Dict[str, Any]] = []
    providers_sync_complete = True
    for pool in raw_pools:
        pool_name = pool.get("name")
        if not pool_name:
            continue
        if pool.get("mode") == _SYSTEM_TRUST_DOMAIN_MODE:
            # GKE-managed pools cannot list providers (the API rejects with
            # 400 INVALID_ARGUMENT). They have no user-managed providers to
            # ingest, so skip the call entirely without flipping the
            # completeness flag.
            logger.debug(
                "Skipping provider listing for SYSTEM_TRUST_DOMAIN pool %s",
                pool_name,
            )
            continue
        try:
            raw_providers = get_workload_identity_providers(iam_client, pool_name)
        except HttpError as e:
            # Mark the run as partial so cleanup does not delete providers
            # under this pool. The next successful run will fully reconcile.
            providers_sync_complete = False
            logger.warning(
                "Failed to list providers for WIF pool %s: %s. Skipping "
                "and disabling provider cleanup for project %s.",
                pool_name,
                e,
                project_id,
            )
            continue
        all_providers.extend(transform_providers(raw_providers, pool, project_id))

    load_providers(neo4j_session, all_providers, project_id, gcp_update_tag)
    cleanup(
        neo4j_session,
        common_job_parameters,
        providers_sync_complete=providers_sync_complete,
    )
