# AIBOM

The AIBOM module maps AI agent inventory from raw Cisco AIBOM `1.0.0rc4` reports onto production container images already present in Cartography. `AIBOMSource` is the primary scanned-target node, and `AIBOMComponent` represents source-scoped components detected in that scanned image. Each component also keeps a stable `logical_id` so the same conceptual component can be correlated across multiple scanned sources without losing per-source identity.

For report requirements, image-linking behavior, and supported graph scope, see the configuration and schema pages.

```{toctree}
config
schema
```
