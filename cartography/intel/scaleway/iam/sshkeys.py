from typing import Any

import neo4j
import scaleway
from scaleway.iam.v1alpha1 import IamV1Alpha1API
from scaleway.iam.v1alpha1 import SSHKey

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.scaleway.utils import scaleway_obj_to_dict
from cartography.models.scaleway.iam.sshkey import ScalewaySSHKeySchema
from cartography.util import timeit


@timeit
def sync(
    neo4j_session: neo4j.Session,
    client: scaleway.Client,
    common_job_parameters: dict[str, Any],
    org_id: str,
    update_tag: int,
) -> None:
    sshkeys = get(client, org_id)
    formatted_sshkeys = transform_sshkeys(sshkeys)
    load_sshkeys(neo4j_session, formatted_sshkeys, org_id, update_tag)
    cleanup(neo4j_session, common_job_parameters)


@timeit
def get(
    client: scaleway.Client,
    org_id: str,
) -> list[SSHKey]:
    api = IamV1Alpha1API(client)
    return api.list_ssh_keys_all(organization_id=org_id)


def transform_sshkeys(sshkeys: list[SSHKey]) -> list[dict[str, Any]]:
    return [scaleway_obj_to_dict(sshkey) for sshkey in sshkeys]


@timeit
def load_sshkeys(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    org_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        ScalewaySSHKeySchema(),
        data,
        lastupdated=update_tag,
        ORG_ID=org_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    GraphJob.from_node_schema(ScalewaySSHKeySchema(), common_job_parameters).run(
        neo4j_session
    )
