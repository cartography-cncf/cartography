# Kubernetes

The Kubernetes module ingests cluster inventory, workloads, networking resources,
secrets metadata, and RBAC identities and permissions. It also connects Kubernetes
resources to cloud infrastructure, container images, and shared ontology labels so
that workload and identity paths can be queried across providers.

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
