# CVE Configuration

:::{important} Deprecated Module
The `cve` module is a standalone legacy importer scheduled for removal in
Cartography v1.0.0. New deployments should use vulnerability-scanner modules
together with [CVE Metadata](../cve_metadata/config.md).
:::

## Authentication

An NVD API key is optional. To use one, store it in an environment variable and
pass that variable's name with `--cve-api-key-env-var`.

## Configure Cartography

The module does not run unless `--cve-enabled` is set, even when `cve` appears
in `--selected-modules`.

Cartography uses `https://services.nvd.nist.gov/rest/json/cves/2.0/` by
default. Override the NVD API base URL with `--nist-cve-url` only when using a
compatible proxy or endpoint.

## Run Cartography

Without an API key:

```bash
cartography \
  --selected-modules cve \
  --cve-enabled
```

With an API key:

```bash
export NVD_API_KEY="<key>"

cartography \
  --selected-modules cve \
  --cve-enabled \
  --cve-api-key-env-var NVD_API_KEY
```

## References

- [NIST NVD API v2.0](https://nvd.nist.gov/developers/vulnerabilities)
