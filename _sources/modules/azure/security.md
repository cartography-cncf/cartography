# Azure Network Security Analysis

## Network Security Rules

Cartography ingests user-defined and platform-default network security group
rules. Every rule carries the shared `IpRule` label and either
`IpPermissionInbound` or `IpPermissionEgress`, according to its direction.
This allows cross-cloud analysis alongside AWS and GCP network rules.

Inbound allow rules with wildcard internet sources such as `*`, `Internet`, or
`0.0.0.0/0` can expose workloads when their destination ranges cover
management or data-service ports such as 22, 3389, 1433, 3306, 5432, or 6379.
Rule priority, protocol, access, source and destination ranges, and whether a
rule is platform-defined are available as node properties.

## Azure Firewall

Azure Firewall nodes expose the configuration needed for network security
analysis:

- `threat_intel_mode` controls Microsoft threat-intelligence filtering.
- `application_rule_collections` captures layer 7 rules with FQDNs and ports.
- `network_rule_collections` captures layer 4 rules with addresses, protocols,
  and ports.
- `nat_rule_collections` captures destination NAT exposure.
- `ip_groups_detail` captures reusable IP address collections.

Firewall IP configurations connect each firewall to its subnet and public IP.
The private address identifies the internal routing endpoint, while the public
address represents outbound and management connectivity.

## Firewall Policies

Firewall policies expose inherited policy configuration and centralized rule
groups. Important security properties include:

- `threat_intel_mode` and `intrusion_detection_mode`
- `rule_groups_detail`, including network, application, and NAT rules
- `dns_servers` and `dns_enable_proxy`
- `snat_private_ranges`
- `transport_security_ca_name`
- threat-intelligence IP and FQDN allowlists

These properties support analysis of policy inheritance, traffic inspection,
name resolution, source NAT exclusions, and encrypted-traffic inspection.
