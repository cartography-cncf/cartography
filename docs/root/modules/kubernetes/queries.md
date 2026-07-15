## Kubernetes Queries

These examples show how to inspect Kubernetes data after a successful sync.

### Inspect kubeconfig TLS posture

Use the TLS posture fields on each cluster to find kubeconfig contexts that skip
verification or lack certificate authority material:

```cypher
MATCH (k:KubernetesCluster)
RETURN k.name, k.api_server_url, k.kubeconfig_tls_configuration_status,
       k.kubeconfig_insecure_skip_tls_verify,
       k.kubeconfig_has_certificate_authority_data,
       k.kubeconfig_has_certificate_authority_file,
       k.kubeconfig_has_client_certificate,
       k.kubeconfig_has_client_key
ORDER BY k.name;
```
