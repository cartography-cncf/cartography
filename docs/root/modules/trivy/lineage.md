## Trivy Image Lineage and Layers

Cartography derives container image lineage by ingesting Trivy scan results and modeling each image's uncompressed rootfs diff ID sequence as a shared graph of `ImageLayer` nodes. This enables us to compute "BUILT_FROM" relationships between images and attribute packages to the layer that introduced them.

### Data sources

From each Trivy JSON document we read:
- `Metadata.rootfs.diff_ids` (preferred) or `Metadata.DiffIDs` — ordered list of uncompressed layer diff IDs
- `Metadata.RepoDigests[0]` — the canonical image digest used as the `ECRImage.id`
- Optional per-vulnerability package `Layer.DiffID` for layer attribution

### Graph model

- Nodes: `(:ImageLayer {id: diff_id, diff_id})`
- Edges:
  - `(:ImageLayer)-[:NEXT]->(:ImageLayer)` connecting adjacent diff IDs in build order
  - `(ECRImage)-[:HEAD]->(:ImageLayer)` to the first diff ID
  - `(ECRImage)-[:TAIL]->(:ImageLayer)` to the last diff ID
  - `(Package)-[:INTRODUCED_IN]->(:ImageLayer)` when a package includes `Layer.DiffID`
- Image property:
  - `ECRImage.length = size(diff_ids)`

All relationships above are created via the Cartography data model (no MatchLinks). Layers are shared across images (MERGE by `diff_id`).

### Lineage algorithm (longest prefix base)

Definition: image B is considered a base of image A if and only if B's diff ID sequence is a strict prefix of A's sequence. If multiple such B exist, pick the one with the largest length.

Implementation steps for an image `image_id`:
1. Starting from its `HEAD`, traverse along `[:NEXT*0..]` to each layer `x`.
2. Find any `(base:ECRImage)-[:TAIL]->(x)` where `length(path) = base.length - 1` and `base.id <> image_id`.
3. Order by `base.length DESC` and pick the first.
4. `MERGE (child:ECRImage {id: image_id})-[:BUILT_FROM]->(base)`.

This computation is performed per image immediately after loading its layers; it is idempotent and avoids N^2 operations across images.

### Cleanup behavior

Image layers are shared across images and should not be deleted during standard cleanup. We therefore:
- Set `scoped_cleanup = False` on `ImageLayerSchema`.
- Implement a bespoke cleanup that:
  - Removes stale `NEXT` edges around layers updated in the current run (those where either endpoint's `lastupdated = UPDATE_TAG`).
  - Removes stale `HEAD`/`TAIL` edges pointing to layers updated this run where the relationship `lastupdated <> UPDATE_TAG`.
  - Deletes orphan `ImageLayer` nodes not updated in this run that have no `NEXT`, `HEAD`, `TAIL`, or `INTRODUCED_IN` relationships.

This strategy keeps frequently referenced layers stable and prunes truly orphaned nodes and stale edges.

### Edge cases and notes

- If `diff_ids` are missing or empty in a scan, we skip layer and lineage writes but still ingest findings/packages/fixes.
- Layers are MERGEd by `diff_id`, so the graph naturally de-duplicates and shares layers.
- Lineage requires at least one common prefix layer; images with different first layers will have no `BUILT_FROM` edge.
- The module uses Trivy vulnerability entries to derive packages; if you enable Trivy's package inventory output, the loader still maintains `DEPLOYED` and `INTRODUCED_IN` where `Layer.DiffID` is present.

