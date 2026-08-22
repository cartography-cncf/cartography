# External Container Images

```{toctree}
schema
```

Cartography resolves explicit public-registry image references into provider-neutral,
digest-keyed artifacts. Mutable tags are kept as separate reference nodes, while manifest
lists contain only runnable platform images. Attestations and image layers are not ingested.

Registry failures are non-destructive. The loader performs no broad node cleanup and only
replaces an old `IMAGE` edge for a tag that was successfully refreshed. Immutable artifacts,
digest references, and `CONTAINS_IMAGE` edges are append-only.

Railway service instances expose their successfully resolved configured reference through
`HAS_IMAGE`; the reference's `IMAGE` edge identifies the current artifact. A current Railway
deployment links directly to an artifact only when its configuration is explicitly
digest-pinned, because a tag lookup does not prove which artifact a deployment ran.
