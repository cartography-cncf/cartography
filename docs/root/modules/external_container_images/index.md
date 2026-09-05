# External Container Images

```{toctree}
schema
```

Cartography resolves explicit anonymous HTTPS public-registry image references into
provider-neutral, digest-keyed artifacts. It does not use private-registry credentials.
Environment credentials, cookies, and HTTP proxy settings are ignored.
Mutable tags are kept as separate reference nodes, while manifest lists contain only
runnable platform images. Attestations and image layers are not ingested.

Registry failures are non-destructive. The loader performs no broad node cleanup and only
replaces an old `IMAGE` edge for a tag that was successfully refreshed. Immutable artifacts,
digest references, and `CONTAINS_IMAGE` edges are append-only.

Railway service instances expose their successfully resolved configured reference through
`HAS_IMAGE`; the reference's `IMAGE` edge identifies the current artifact. Only the latest
Railway deployment, when it is active or sleeping, links directly to an artifact, and only
when its configuration is explicitly digest-pinned. A tag lookup does not prove which
artifact a deployment ran.
