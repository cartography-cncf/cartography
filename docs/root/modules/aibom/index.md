# AIBOM

The AIBOM module maps AI agent inventory onto production container images. It preserves source-level provenance, workflow context, and query-friendly component relationships such as `USES_TOOL` and `USES_MODEL`. `AIBOMSource` is the primary scanned-target node and links to any node carrying the `:Image` ontology label resolved from the source image URI, while each `AIBOMComponent` keeps both an occurrence-oriented `id` and a stable `logical_id` so repeated rebuilds of the same code can be grouped without losing per-image fidelity. The logical fingerprint intentionally excludes scanner-specific metadata such as `label` and dependency-specific metadata such as `model_name`.

```{toctree}
config
schema
```
