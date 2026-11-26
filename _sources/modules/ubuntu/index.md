# Ubuntu Security

The Ubuntu Security module ingests the public Ubuntu CVE feed and Ubuntu
Security Notices. It creates feed, CVE, and notice nodes and connects notices
to the CVEs they address.

The first successful run performs a full paginated sync. Later runs request
CVEs updated since the last stored watermark and notices published since the
last stored watermark. Interrupted full syncs resume from their saved offset.

See [configuration](config.md) to enable the module and the generated
[schema](schema.md) for node properties and relationships.

```{toctree}
config
schema
```
