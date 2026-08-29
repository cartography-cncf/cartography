# Kubernetes

The Kubernetes module ingests cluster inventory, GPU capacity and requests,
persistent storage, workloads, networking resources, secrets metadata, and RBAC
identities and permissions. It also connects Kubernetes resources to cloud
infrastructure, container images, and shared ontology labels so that workload and
identity paths can be queried across providers.

PersistentVolumes managed by the AWS EBS or Azure Disk CSI drivers connect to
already-ingested cloud disks with `BACKED_BY` relationships.

Container `MOUNTS` relationships identify the PersistentVolumeClaims used by
individual containers. Each container's `persistent_volume_claim_mounts`
property preserves the claim identifier, mount path, read-only setting, and
other per-mount Kubernetes configuration as a JSON-encoded list. The
`persistent_volume_claim_read_write_ids` property provides a queryable list of
claims that have at least one read-write mount.

For raw block volumes, container `USES_BLOCK_DEVICE` relationships and the
`persistent_volume_claim_devices` property preserve the claim identifier and
device path. Pod `REFERENCES` relationships identify claims declared by pod
volumes, including claims that no container mounts.

Container storage relationships currently cover regular application containers
in `spec.containers`. Init containers and ephemeral containers aren't modeled as
`KubernetesContainer` nodes.

Use the configuration guide to grant read-only access and connect one or more
clusters. The schema reference is generated from the model definitions and is
included automatically in the built documentation. The query guide contains
operational examples for inspecting the resulting graph.

## Optional permission behavior

When Gateway API CRDs are absent, Cartography treats Gateway API inventory as
empty and cleans stale `KubernetesGateway` and `KubernetesHTTPRoute` nodes. If
the CRDs exist but the identity cannot list them, Cartography skips ingestion
and cleanup, preserving existing nodes. Ingested gateways and HTTP routes form
the `Gateway -[:ROUTES]-> HTTPRoute -[:TARGETS]-> Service` traffic path.

If the identity cannot list network policies, Cartography skips both ingestion
and cleanup and preserves existing `KubernetesNetworkPolicy` nodes. Ingested
policies use `APPLIES_TO` edges to identify selected pods.

Until v1.0.0, if the identity cannot list persistent volumes, persistent volume
claims, or storage classes, Cartography skips persistent storage ingestion and
cleanup and preserves existing storage nodes. Pods continue to load. On a first
sync, pods have no `REFERENCES` relationships and containers have no `MOUNTS` or
`USES_BLOCK_DEVICE` relationships. After an earlier successful storage sync,
pods and containers can link to the preserved storage snapshot, which may be
stale until permissions are restored.

If the identity cannot list secrets, Cartography skips secret ingestion and
cleanup and preserves existing `KubernetesSecret` nodes. Cartography stores
only secret metadata, never secret content.

For EKS, Cartography reads `mapRoles`, `mapUsers`, and `mapAccounts` from the
legacy `aws-auth` ConfigMap when permitted. Account mappings connect every
already-synced IAM principal from the listed AWS account to a `KubernetesUser`
named for the principal ARN. Without the ConfigMap, Access Entries and external
OIDC mappings still load, but stale identity cleanup removes mappings that were
previously supplied only by `aws-auth`.

```{toctree}
config
queries
schema
```
