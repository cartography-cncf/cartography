import logging
from typing import Any

import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.ontology.runtime_image import RuntimeImageSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)

_RUNTIME_IMAGES_QUERY = """
CALL {
    MATCH (workload:Container)
    WHERE toLower(coalesce(workload._ont_state, '')) = 'running'
    RETURN workload, 'container' AS workload_kind

    UNION

    MATCH (workload:Function)
    WHERE workload._ont_deployment_type = 'container'
    RETURN workload, 'function' AS workload_kind
}
WITH workload, workload_kind
WHERE workload._ont_image IS NOT NULL
  AND trim(workload._ont_image) <> ''
  AND workload._ont_image_digest IS NOT NULL
  AND trim(workload._ont_image_digest) <> ''
  AND NOT EXISTS {
      MATCH (workload)-[:HAS_IMAGE]->(existing:Image)
      WHERE NOT existing:RuntimeImage
        AND coalesce(existing._ont_digest, existing.digest) = workload._ont_image_digest
  }
WITH workload._ont_image_digest AS digest,
     collect(DISTINCT workload._ont_image) AS runtime_refs,
     collect(DISTINCT CASE WHEN workload_kind = 'container' THEN workload.id END) AS raw_container_ids,
     collect(DISTINCT CASE WHEN workload_kind = 'function' THEN workload.id END) AS raw_function_ids
RETURN digest,
       runtime_refs,
       [id IN raw_container_ids WHERE id IS NOT NULL] AS container_ids,
       [id IN raw_function_ids WHERE id IS NOT NULL] AS function_ids
ORDER BY digest
"""


def _digest_ref(image_ref: str, digest: str) -> str:
    repository = image_ref.split("@", 1)[0]
    last_slash = repository.rfind("/")
    last_colon = repository.rfind(":")
    if last_colon > last_slash:
        repository = repository[:last_colon]
    return f"{repository}@{digest}"


def get_runtime_images(neo4j_session: neo4j.Session) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for record in neo4j_session.run(_RUNTIME_IMAGES_QUERY):
        digest = record["digest"].strip()
        runtime_refs = sorted(
            {
                ref.strip()
                for ref in record["runtime_refs"]
                if isinstance(ref, str) and ref.strip()
            },
        )
        if not runtime_refs:
            continue
        rows.append(
            {
                "id": f"runtime-image:{digest}",
                "digest": digest,
                "uri": _digest_ref(runtime_refs[0], digest),
                "runtime_refs": runtime_refs,
                "container_ids": record["container_ids"],
                "function_ids": record["function_ids"],
            },
        )
    return rows


@timeit
def sync(
    neo4j_session: neo4j.Session,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    runtime_images = get_runtime_images(neo4j_session)
    load(
        neo4j_session,
        RuntimeImageSchema(),
        runtime_images,
        lastupdated=update_tag,
    )
    GraphJob.from_node_schema(RuntimeImageSchema(), common_job_parameters).run(
        neo4j_session,
    )
    logger.info("Loaded %d runtime image(s)", len(runtime_images))
