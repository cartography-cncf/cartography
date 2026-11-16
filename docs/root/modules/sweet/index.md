# Sweet Security

```{toctree}
config
schema
```

[Sweet Security](https://www.sweet.security) is a runtime cloud security
platform that runs an eBPF sensor on workloads. Cartography ingests the state
that Sweet builds from that runtime data, not the raw event stream:

- **AWS connections.** Each AWS account and organization connected to Sweet
  becomes a `SweetAWSAccount` or `SweetAWSOrganization` node. It links with
  `MONITORS` to the `AWSAccount` it covers, so you can find AWS accounts
  that Sweet does not monitor. An organization connection links to the
  organization's management account only.
- **Runtime vulnerabilities.** Each open, in-progress, or ignored vulnerability
  becomes a `SweetVulnerability` node. It records when Sweet last saw the
  vulnerable package loaded into memory (`last_loaded`) or executing
  (`last_executed`). This shows whether the vulnerable code actually runs,
  which static scanners cannot tell you. A vulnerability whose identifier is
  a CVE carries the `CVE` ontology label and links with `LINKED_TO` to the
  `CVE` node. It also links with `AFFECTS` to every synced container `Image`
  with the same digest.
- **Attack chains.** Each open or in-progress attack chain becomes a
  `SweetAttackChain` node with the `SecurityIssue` ontology label. It links
  with `AFFECTS` to every synced `DNSRecord` whose name is the chain's
  endpoint host.

Resolved vulnerabilities and resolved or closed attack chains are not
ingested. After each sync, cleanup removes the ones that were resolved since
the previous sync.

The module does not ingest Investigator events (raw sensor and cloud log
events), incidents, the package inventory, or registry configuration.

Sweet runs after the cloud provider modules in a default sync, so the
`AWSAccount`, `Image`, and `DNSRecord` nodes that it links to already exist.
