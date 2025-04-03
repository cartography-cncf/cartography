## CVE Configuration

Follow these steps to analyze CVE objects with Cartography.

1. Set the `CARTOGRAPHY_CVE__ENABLED=True` variable.
1. If you are mirroring the CVE data, and wish to change the base url, you can pass the base url into the cli with the `CARTOGRAPHY_CVE__URL` variable.

### Cartography Configuration

| Name | Type     | Description |
|------|----------|-------------|
| CARTOGRAPHY_CVE__ENABLED | `bool` _(default: False)_ | If set, CVE data will be synced from NIST. |
| CARTOGRAPHY_CVE__URL | `str` | The base url for the NIST CVE data. Default = https://services.nvd.nist.gov/rest/json/cves/2.0/' |
| CARTOGRAPHY_CVE__API_KEY | `str` | If set, uses the provided NIST NVD API v2.0 key. |
