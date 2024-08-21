import logging
from typing import Any
from typing import Dict
from typing import List

import neo4j

from .util import call_snipeit_api
from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.snipeit.asset import SnipeitAssetSchema
from cartography.models.snipeit.tenant import SnipeitTenantSchema
from cartography.util import timeit


logger = logging.getLogger(__name__)


@timeit
def get(base_uri: str, token: str) -> List[Dict]:
    api_endpoint = "/api/v1/hardware"
    results: List[Dict[str, Any]] = []
    while True:
        offset = len(results)
        api_endpoint = f"{api_endpoint}?order='asc'&offset={offset}"
        response = call_snipeit_api(api_endpoint, base_uri, token)
        results.extend(response['rows'])

        total = response['total']
        results_count = len(results)
        if results_count >= total:
            break

    return results


@timeit
def load_assets(
    neo4j_session: neo4j.Session,
    common_job_parameters: Dict,
    data: List[Dict[str, Any]],
) -> None:
    # Create the SnipeIT Tenant
    load(
        neo4j_session,
        SnipeitTenantSchema(),
        [{'id': common_job_parameters["TENANT_ID"]}],
        lastupdated=common_job_parameters["UPDATE_TAG"],
    )

    load(
        neo4j_session,
        SnipeitAssetSchema(),
        data,
        lastupdated=common_job_parameters["UPDATE_TAG"],
        TENANT_ID=common_job_parameters["TENANT_ID"],
    )


@timeit
def cleanup(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    GraphJob.from_node_schema(SnipeitAssetSchema(), common_job_parameters).run(neo4j_session)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    common_job_parameters: Dict,
    base_uri: str,
    token: str,
) -> None:
    assets = get(base_uri=base_uri, token=token)
    load_assets(neo4j_session=neo4j_session, common_job_parameters=common_job_parameters, data=assets)
    cleanup(neo4j_session, common_job_parameters)
