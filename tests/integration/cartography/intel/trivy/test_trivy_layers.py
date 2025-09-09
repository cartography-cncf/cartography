import copy
from typing import Any
from typing import cast
from typing import Dict
from typing import List

from neo4j import Session

from tests.data.trivy.trivy_sample import TRIVY_SAMPLE

TEST_UPDATE_TAG = 987654321


def test_trivy_layers_and_lineage_from_sample(neo4j_session: Session) -> None:
    """Test image layer and lineage creation from mock Trivy data."""
    # Base doc from sample
    base_doc: Dict[str, Any] = cast(Dict[str, Any], copy.deepcopy(TRIVY_SAMPLE))
    base_metadata: Dict[str, Any] = cast(Dict[str, Any], base_doc["Metadata"])
    base_digest = str(base_metadata["RepoDigests"][0]).split("@")[1]
    rootfs = cast(Dict[str, Any], base_metadata.get("rootfs", {}))
    base_diff_ids: List[str] = (
        cast(List[str], rootfs.get("diff_ids"))
        or cast(
            List[str],
            base_metadata.get("DiffIDs"),
        )
        or []
    )

    # Derived doc extends base diff_ids by one layer
    child_doc: Dict[str, Any] = copy.deepcopy(base_doc)
    child_digest = (
        "sha256:eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee"
    )
    new_tail = "sha256:ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff"
    child_diff_ids: List[str] = base_diff_ids + [new_tail]
    child_metadata: Dict[str, Any] = child_doc["Metadata"]
    child_repo_digests: List[str] = cast(List[str], child_metadata["RepoDigests"])
    child_repo_digests[0] = f"example.com/repo@{child_digest}"
    # Update both places Trivy may store diff IDs
    if "rootfs" in child_metadata:
        child_rootfs: Dict[str, Any] = cast(Dict[str, Any], child_metadata["rootfs"])
        child_rootfs["diff_ids"] = child_diff_ids
    child_metadata["DiffIDs"] = child_diff_ids

    # Negative doc with different first layer
    other_doc: Dict[str, Any] = copy.deepcopy(base_doc)
    other_digest = (
        "sha256:dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd"
    )
    other_first = (
        "sha256:xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
    )
    other_diff_ids: List[str] = [other_first] + base_diff_ids[
        1:3
    ]  # short, different start
    other_metadata: Dict[str, Any] = other_doc["Metadata"]
    other_repo_digests: List[str] = cast(List[str], other_metadata["RepoDigests"])
    other_repo_digests[0] = f"example.com/other@{other_digest}"
    if "rootfs" in other_metadata:
        other_rootfs: Dict[str, Any] = cast(Dict[str, Any], other_metadata["rootfs"])
        other_rootfs["diff_ids"] = other_diff_ids
    other_metadata["DiffIDs"] = other_diff_ids

    # Act: process base, child, other
    # Seed required ECRImage nodes so relationships can be created by the model
    neo4j_session.run(
        """
        UNWIND $ids AS id
        MERGE (:ECRImage {id: id})
        """,
        ids=[base_digest, child_digest, other_digest],
    )

    # Build layers directly from mock data
    # Note: In real usage, this would fetch from registry
    # Here we simulate by directly loading the mock diff_ids

    # Load image layers
    if base_diff_ids:
        from cartography.client.core.tx import load
        from cartography.models.trivy.image_layer import ImageLayerSchema

        for image_id, diff_ids in [
            (base_digest, base_diff_ids),
            (child_digest, child_diff_ids),
            (other_digest, other_diff_ids),
        ]:
            records = []
            for i, diff_id in enumerate(diff_ids):
                rec: Dict[str, Any] = {"diff_id": diff_id}
                if i < len(diff_ids) - 1:
                    rec["next_diff_id"] = diff_ids[i + 1]
                if i == 0:
                    rec["head_image_ids"] = [image_id]
                if i == len(diff_ids) - 1:
                    rec["tail_image_ids"] = [image_id]
                records.append(rec)

            load(
                neo4j_session,
                ImageLayerSchema(),
                records,
                lastupdated=TEST_UPDATE_TAG,
            )

            # Update ECRImage length
            neo4j_session.run(
                "MATCH (img:ECRImage {id: $id}) SET img.length = $length",
                id=image_id,
                length=len(diff_ids),
            )

    # Compute lineage relationships
    from cartography.intel.trivy.layers import compute_image_lineage

    # Check lineage and create relationships
    if compute_image_lineage(base_diff_ids, child_diff_ids):
        # Create BUILT_FROM for ECRImage nodes
        neo4j_session.run(
            "MATCH (c:ECRImage {id: $child}), (b:ECRImage {id: $base}) "
            "MERGE (c)-[:BUILT_FROM]->(b)",
            child=child_digest,
            base=base_digest,
        )

    # Assert: layer nodes are unique and shared
    res = neo4j_session.run("MATCH (l:ImageLayer) RETURN count(l) AS c").single()
    assert res["c"] == len(set(base_diff_ids)) + 2  # new_tail + other_first

    # Assert: image length and HEAD/TAIL
    rows = neo4j_session.run(
        """
        MATCH (i:ECRImage)-[:HEAD]->(h:ImageLayer)
        MATCH (i)-[:TAIL]->(t:ImageLayer)
        WHERE i.id IN $ids
        RETURN i.id AS id, i.length AS length, h.diff_id AS head, t.diff_id AS tail
        """,
        ids=[base_digest, child_digest, other_digest],
    ).data()
    m = {r["id"]: r for r in rows}
    assert m[base_digest]["length"] == len(base_diff_ids)
    assert m[base_digest]["head"] == base_diff_ids[0]
    assert m[base_digest]["tail"] == base_diff_ids[-1]
    assert m[child_digest]["length"] == len(child_diff_ids)
    assert m[child_digest]["head"] == base_diff_ids[0]
    assert m[child_digest]["tail"] == new_tail
    assert m[other_digest]["length"] == len(other_diff_ids)
    assert m[other_digest]["head"] == other_first
    assert m[other_digest]["tail"] == other_diff_ids[-1]

    # Assert: lineage child -> base, but not other -> base
    built = neo4j_session.run(
        "MATCH (c:ECRImage)-[:BUILT_FROM]->(b:ECRImage) RETURN c.id AS c, b.id AS b"
    ).data()
    pairs = {(r["c"], r["b"]) for r in built}
    assert (child_digest, base_digest) in pairs
    assert (other_digest, base_digest) not in pairs

    # Note: Package INTRODUCED_IN edges are no longer created in the lineage module
    # They would be created separately during vulnerability scanning if needed
