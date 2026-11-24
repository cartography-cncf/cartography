# Crowdstrike

```{toctree}
config
schema
```

Spotlight reports each vulnerability once per host. Cartography also groups
those rows by the application they affect, such as `.Net Framework 4.8`, into
one `CrowdstrikeApplication` per tenant and application version:

```
(:CrowdstrikeFinding)-[:AFFECTS]->(:CrowdstrikeApplication)-[:DEPLOYED]->(:CrowdstrikeHost)
```

When Spotlight reports a version after the product name, the ontology packages
sync maps the application to a `PackageVersion`. A CVE then reaches the devices
it affects through `(:CVE)-[:AFFECTS]->(:PackageVersion)-[:DEPLOYED]->(:Device)`,
one edge per application and device rather than one per CVE and host.
Applications that Spotlight reports without a version, such as `Windows Server
2022`, keep their `CrowdstrikeApplication` node but get no `PackageVersion`.
