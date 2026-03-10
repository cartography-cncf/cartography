# AIBOM

The AIBOM module maps AI agent inventory onto production container images. It preserves scan provenance, source-level structure, component detections, workflow context, and query-friendly component relationships such as `USES_TOOL` and `USES_MODEL`. Each `AIBOMComponent` keeps both an occurrence-oriented `id` and a stable `logical_id` so repeated rebuilds of the same code can be grouped without losing per-image fidelity.

```{toctree}
config
schema
```
