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

See [configuration](config.md) for setup and input requirements, the generated
[schema](schema.md) for graph fields and relationships, and
[examples](examples.md) for queries.

```{toctree}
config
schema
examples
```
