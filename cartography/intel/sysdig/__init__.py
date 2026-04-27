import logging
from datetime import datetime
from datetime import timedelta
from datetime import timezone
from typing import Any

import neo4j

from cartography.client.core.tx import load
from cartography.config import Config
from cartography.graph.job import GraphJob
from cartography.intel.sysdig.client import schema_has_entity
from cartography.intel.sysdig.client import SysdigClient
from cartography.intel.sysdig.transform import normalize_tenant_id
from cartography.intel.sysdig.transform import transform_risk_findings
from cartography.intel.sysdig.transform import transform_runtime_event_summaries
from cartography.intel.sysdig.transform import transform_security_findings
from cartography.intel.sysdig.transform import transform_tenant
from cartography.intel.sysdig.transform import transform_vulnerabilities
from cartography.models.sysdig import SysdigImageSchema
from cartography.models.sysdig import SysdigPackageSchema
from cartography.models.sysdig import SysdigResourceSchema
from cartography.models.sysdig import SysdigRiskFindingSchema
from cartography.models.sysdig import SysdigRuntimeEventSummarySchema
from cartography.models.sysdig import SysdigSecurityFindingSchema
from cartography.models.sysdig import SysdigTenantSchema
from cartography.models.sysdig import SysdigVulnerabilityFindingSchema
from cartography.stats import get_stats_client
from cartography.util import merge_module_sync_metadata
from cartography.util import timeit

logger = logging.getLogger(__name__)
stat_handler = get_stats_client(__name__)

VULNERABILITY_QUERY = """
MATCH {root} AS resource AFFECTED_BY Vulnerability AS vulnerability
OPTIONAL MATCH Vulnerability AS vulnerability AFFECTS Package AS package
RETURN resource, vulnerability, package
"""

RISK_QUERY = """
MATCH {root} AS resource AFFECTED_BY RiskFinding AS finding
RETURN resource, finding
"""

SECURITY_FINDING_QUERY = """
MATCH {root} AS resource AFFECTED_BY {entity} AS finding
RETURN resource, finding
"""

RUNTIME_EVENT_QUERY = """
MATCH {root} AS resource
OPTIONAL MATCH RuntimeEvent AS event GENERATED_BY resource
WHERE event.timestamp >= '{cutoff}'
RETURN event, resource
"""

RESOURCE_ROOT_ENTITIES = (
    "KubeWorkload",
    "KubePod",
    "KubeNode",
    "KubeCluster",
    "KubeNamespace",
    "KubeDeployment",
    "KubeDaemonSet",
    "KubeStatefulSet",
    "ContainerImage",
    "CloudResource",
    "AWSResource",
    "AWSAccount",
    "GCPResource",
    "GCPProject",
    "AzureResource",
    "AzureSubscription",
    "EC2Instance",
)

SECURITY_FINDING_ENTITIES = (
    "PostureFinding",
    "ComplianceFinding",
    "SecurityFinding",
)


@timeit
def start_sysdig_ingestion(
    neo4j_session: neo4j.Session,
    config: Config,
) -> None:
    if not config.sysdig_api_token:
        logger.info("Sysdig API token not configured; skipping Sysdig sync")
        return

    tenant_id = config.sysdig_tenant_id or normalize_tenant_id(config.sysdig_api_url)
    common_job_parameters = {
        "UPDATE_TAG": config.update_tag,
        "TENANT_ID": tenant_id,
    }

    client = SysdigClient(
        config.sysdig_api_url,
        config.sysdig_api_token,
        page_size=config.sysdig_page_size,
    )
    sync(
        neo4j_session,
        client,
        config.sysdig_api_url,
        tenant_id,
        config.update_tag,
        config.sysdig_runtime_event_lookback_hours,
        common_job_parameters,
    )

    merge_module_sync_metadata(
        neo4j_session,
        group_type="sysdig",
        group_id=tenant_id,
        synced_type="sysdig",
        update_tag=config.update_tag,
        stat_handler=stat_handler,
    )


@timeit
def sync(
    neo4j_session: neo4j.Session,
    client: SysdigClient,
    api_url: str,
    tenant_id: str,
    update_tag: int,
    runtime_event_lookback_hours: int,
    common_job_parameters: dict[str, Any],
) -> None:
    schema = client.get_schema()
    common_job_parameters["TENANT_ID"] = tenant_id
    load_sysdig_data(
        neo4j_session,
        SysdigTenantSchema(),
        transform_tenant(api_url, tenant_id),
        update_tag,
    )

    if schema_has_entity(schema, "Vulnerability"):
        vuln_rows = query_resource_roots(client, schema, VULNERABILITY_QUERY)
        resources, images, packages, findings = transform_vulnerabilities(
            vuln_rows,
            tenant_id,
        )
        load_sysdig_data(
            neo4j_session, SysdigResourceSchema(), resources, update_tag, tenant_id
        )
        load_sysdig_data(
            neo4j_session, SysdigImageSchema(), images, update_tag, tenant_id
        )
        load_sysdig_data(
            neo4j_session, SysdigPackageSchema(), packages, update_tag, tenant_id
        )
        load_sysdig_data(
            neo4j_session,
            SysdigVulnerabilityFindingSchema(),
            findings,
            update_tag,
            tenant_id,
        )

    if schema_has_entity(schema, "RiskFinding"):
        risk_rows = query_resource_roots(client, schema, RISK_QUERY)
        resources, findings = transform_risk_findings(risk_rows, tenant_id)
        load_sysdig_data(
            neo4j_session, SysdigResourceSchema(), resources, update_tag, tenant_id
        )
        load_sysdig_data(
            neo4j_session,
            SysdigRiskFindingSchema(),
            findings,
            update_tag,
            tenant_id,
        )

    for entity in SECURITY_FINDING_ENTITIES:
        if not schema_has_entity(schema, entity):
            continue
        security_rows = query_resource_roots(
            client,
            schema,
            SECURITY_FINDING_QUERY,
            entity=entity,
        )
        resources, findings = transform_security_findings(
            security_rows,
            tenant_id,
            entity,
        )
        load_sysdig_data(
            neo4j_session, SysdigResourceSchema(), resources, update_tag, tenant_id
        )
        load_sysdig_data(
            neo4j_session,
            SysdigSecurityFindingSchema(),
            findings,
            update_tag,
            tenant_id,
        )

    if schema_has_entity(schema, "RuntimeEvent"):
        cutoff = (
            datetime.now(timezone.utc) - timedelta(hours=runtime_event_lookback_hours)
        ).isoformat()
        runtime_rows = query_resource_roots(
            client,
            schema,
            RUNTIME_EVENT_QUERY,
            cutoff=cutoff,
        )
        resources, summaries = transform_runtime_event_summaries(
            runtime_rows, tenant_id
        )
        load_sysdig_data(
            neo4j_session, SysdigResourceSchema(), resources, update_tag, tenant_id
        )
        load_sysdig_data(
            neo4j_session,
            SysdigRuntimeEventSummarySchema(),
            summaries,
            update_tag,
            tenant_id,
        )

    cleanup(neo4j_session, common_job_parameters)


def query_resource_roots(
    client: SysdigClient,
    schema: dict[str, Any],
    query_template: str,
    **format_kwargs: Any,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for root in RESOURCE_ROOT_ENTITIES:
        if not schema_has_entity(schema, root):
            continue
        rows.extend(client.query(query_template.format(root=root, **format_kwargs)))
    return rows


def load_sysdig_data(
    neo4j_session: neo4j.Session,
    schema: Any,
    data: list[dict[str, Any]],
    update_tag: int,
    tenant_id: str | None = None,
) -> None:
    if not data:
        return
    kwargs: dict[str, Any] = {"lastupdated": update_tag}
    if tenant_id is not None:
        kwargs["TENANT_ID"] = tenant_id
    load(neo4j_session, schema, data, **kwargs)


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    for schema in (
        SysdigVulnerabilityFindingSchema(),
        SysdigSecurityFindingSchema(),
        SysdigRiskFindingSchema(),
        SysdigRuntimeEventSummarySchema(),
        SysdigPackageSchema(),
        SysdigImageSchema(),
        SysdigResourceSchema(),
        SysdigTenantSchema(),
    ):
        GraphJob.from_node_schema(schema, common_job_parameters).run(neo4j_session)
