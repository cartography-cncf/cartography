# AIBOM

The AIBOM module ingests raw Cisco AIBOM `1.0.0rc4` reports and adds an AI
inventory layer to Cartography. It connects agents, models, tools, prompts,
memory layers, embeddings, and other detected components to production
container images or source-code repositories already present in the graph.

Traditional image inventory describes packages and vulnerabilities but not the
AI systems assembled from those packages. AIBOM data supports questions such
as:

- Which production images contain AI agents?
- Which models and tools are used by a component?
- Which repositories contain prompts, memory layers, or embeddings?
- Which equivalent components recur across image rebuilds?

## Graph model

`AIBOMSource` represents one scanned image or repository.
`AIBOMComponent` represents one detected component occurrence within that
source. Sources are anchored to concrete `Image`, `GitHubRepository`, or
`GitLabProject` nodes before their reports are loaded.

Component `id` values include source context and preserve occurrence identity.
The separate `logical_id` property is a stable cross-source fingerprint derived
from component type, name, location, framework, model, storage, and skill
metadata. Use it to correlate equivalent components without merging their
source-specific detections.

The component `category` controls additional graph labels:

- `agent` produces `AIAgent`.
- `model` produces the ontology label `AIModel`.
- `tool` produces `AITool`.
- `memory` produces `AIMemory`.
- `embedding` produces `AIEmbedding`.
- `prompt` produces `AIPrompt`.

Report-defined component relationships are loaded when both endpoints resolve
within the same source. Category-specific metadata remains serialized in
`metadata_json` until those categories receive dedicated first-class models.
Workflow-like context is preserved through component evidence and metadata
rather than separate workflow nodes.

## Target linking behavior

AIBOM validates every source against an existing graph node before loading any
data:

- Digest-qualified image references (`repo@sha256:...`) must match an existing
  `Image._ont_digest`.
- Other source keys are treated as repository URIs and must match
  `GitHubRepository.url` or `GitLabProject.web_url`.
- Tag-only image references (`repo:tag`) do not identify a concrete image and
  are interpreted as repository URIs.
- Manifest lists and image tags are not valid image anchors. Image reports
  must resolve to a concrete `Image` digest.

If any source key fails to resolve, Cartography rejects the entire report
instead of loading a partial source graph.

## Snapshot behavior

The module ingests every `*.json` file under the configured source as one
snapshot. Older reports for the same image are also loaded if they remain in
the source because all reports share the same update tag.

Cleanup is module-wide and runs only after a fully observed snapshot. If any
report cannot be read, Cartography skips cleanup to preserve last-known-good
data.

The module emits the `aibom_reports_processed` observability counter.

See [configuration](config.md) for setup and input requirements, the generated
[schema](schema.md) for graph fields and relationships, and
[examples](examples.md) for queries.

```{toctree}
config
schema
examples
```
