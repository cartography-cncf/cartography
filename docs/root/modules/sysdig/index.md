## Sysdig

The Sysdig module ingests security findings from Sysdig Secure into Cartography.
It is findings-first: it uses Sysdig SysQL to load vulnerability findings,
security/posture findings, risk findings, and aggregated runtime detection
summaries. It does not mirror the full Sysdig inventory and does not ingest raw
Falco event streams.

Primary Sysdig references:

- [SysQL API](https://docs.sysdig.com/en/developer-tools/sysql-api/)
- [SysQL Reference Library](https://docs.sysdig.com/en/sysdig-secure/sysql-reference/)
- [Search](https://docs.sysdig.com/en/sysdig-secure/search/)
- [Risk](https://docs.sysdig.com/en/sysdig-secure/risks/)

See [Configuration](config.md) and [Schema](schema.md).
