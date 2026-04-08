from typing import Any
from typing import AsyncGenerator

import neo4j
from msgraph import GraphServiceClient
from msgraph.generated.models.device_compliance_policy import DeviceCompliancePolicy

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.microsoft.intune.compliance_policy import (
    IntuneCompliancePolicySchema,
)
from cartography.util import timeit

# The @odata.type value tells us the platform since the base class doesn't have it.
_ODATA_TYPE_TO_PLATFORM = {
    "#microsoft.graph.androidCompliancePolicy": "android",
    "#microsoft.graph.androidWorkProfileCompliancePolicy": "androidWorkProfile",
    "#microsoft.graph.iosCompliancePolicy": "ios",
    "#microsoft.graph.macOSCompliancePolicy": "macOS",
    "#microsoft.graph.windows10CompliancePolicy": "windows10",
    "#microsoft.graph.windowsPhone81CompliancePolicy": "windowsPhone81",
}


@timeit
async def get_compliance_policies(
    client: GraphServiceClient,
) -> AsyncGenerator[DeviceCompliancePolicy, None]:
    """
    Get all Intune compliance policies with their assignments expanded inline.
    https://learn.microsoft.com/en-us/graph/api/intune-deviceconfig-devicecompliancepolicy-list
    Permissions: DeviceManagementConfiguration.Read.All
    """
    request_config = client.device_management.device_compliance_policies.DeviceCompliancePoliciesRequestBuilderGetRequestConfiguration(
        query_parameters=client.device_management.device_compliance_policies.DeviceCompliancePoliciesRequestBuilderGetQueryParameters(
            expand=["assignments"],
        ),
    )

    page = await client.device_management.device_compliance_policies.get(
        request_configuration=request_config,
    )
    while page:
        if page.value:
            for policy in page.value:
                yield policy
        if not page.odata_next_link:
            break

        page = await client.device_management.device_compliance_policies.with_url(
            page.odata_next_link,
        ).get()


def transform_compliance_policies(
    policies: list[DeviceCompliancePolicy],
) -> list[dict[str, Any]]:
    """
    Transform compliance policies into dicts matching IntuneCompliancePolicySchema.
    Denormalizes group assignments: one row per (policy, group) pair.
    Policies with no group assignments still produce one row with group_id=None.
    """
    result: list[dict[str, Any]] = []
    for policy in policies:
        odata_type = getattr(policy, "odata_type", None) or ""
        base: dict[str, Any] = {
            "id": policy.id,
            "display_name": policy.display_name,
            "description": policy.description,
            "platform": _ODATA_TYPE_TO_PLATFORM.get(odata_type, odata_type),
            "version": policy.version,
            "created_date_time": policy.created_date_time,
            "last_modified_date_time": policy.last_modified_date_time,
        }

        group_ids: list[str] = []
        applies_to_all_users = False
        applies_to_all_devices = False
        for assignment in policy.assignments or []:
            target = assignment.target
            if target is None:
                continue
            odata_target_type = getattr(target, "odata_type", "") or ""
            if hasattr(target, "group_id") and target.group_id:
                group_ids.append(target.group_id)
            elif "allLicensedUsers" in odata_target_type:
                applies_to_all_users = True
            elif "allDevices" in odata_target_type:
                applies_to_all_devices = True

        base["applies_to_all_users"] = applies_to_all_users
        base["applies_to_all_devices"] = applies_to_all_devices

        if group_ids:
            for group_id in group_ids:
                result.append({**base, "group_id": group_id})
        else:
            result.append({**base, "group_id": None})
    return result


@timeit
def load_compliance_policies(
    neo4j_session: neo4j.Session,
    policies: list[dict[str, Any]],
    tenant_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        IntuneCompliancePolicySchema(),
        policies,
        lastupdated=update_tag,
        TENANT_ID=tenant_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(
        IntuneCompliancePolicySchema(),
        common_job_parameters,
    ).run(neo4j_session)


@timeit
async def sync_compliance_policies(
    neo4j_session: neo4j.Session,
    client: GraphServiceClient,
    tenant_id: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    policies_batch: list[DeviceCompliancePolicy] = []
    batch_size = 500

    async for policy in get_compliance_policies(client):
        policies_batch.append(policy)

        if len(policies_batch) >= batch_size:
            transformed = transform_compliance_policies(policies_batch)
            load_compliance_policies(neo4j_session, transformed, tenant_id, update_tag)
            policies_batch.clear()

    if policies_batch:
        transformed = transform_compliance_policies(policies_batch)
        load_compliance_policies(neo4j_session, transformed, tenant_id, update_tag)

    cleanup(neo4j_session, common_job_parameters)
