# CVE Configuration

:::{important} Deprecated Module
The `cve` module is a deprecated compatibility alias. Use the
[CVE Metadata configuration](../cve_metadata/config.md) for current setup
instructions.
:::

## Legacy Options

These options configure the deprecated `cve` module. New deployments should use
the `--cve-metadata-*` options described in the
[CVE Metadata configuration](../cve_metadata/config.md).

| Option | Description |
|--------|-------------|
| `--cve-enabled` | Enable CVE data sync from NIST. |
| `--cve-api-key-env-var` | Environment variable name containing the NIST NVD API v2.0 key. |
| `--nist-cve-url` | Base URL for NIST CVE data. Default: `https://services.nvd.nist.gov/rest/json/cves/2.0/`. |
