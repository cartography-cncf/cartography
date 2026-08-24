# CVE

:::{important} Deprecated Module
The CVE module is a standalone legacy importer, not an alias for
`cve_metadata`. It is deprecated, no longer receives updates, and is scheduled
for removal in Cartography v1.0.0.
:::

When enabled, this module imports CVE nodes from NIST NVD year archives and
modified-data responses. CVEs are not deleted during cleanup.

The [CVE Metadata](../cve_metadata/index.md) module has a different role: it
enriches CVE nodes created by vulnerability-scanner modules and does not import
every CVE. New deployments should use scanner modules together with
`cve_metadata`. Existing deployments that require a complete NVD CVE inventory
can continue using this legacy module during migration.

```{toctree}
config
schema
```
