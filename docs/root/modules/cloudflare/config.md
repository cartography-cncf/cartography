# Cloudflare Configuration

## Authentication

Create an API token in Cloudflare under `Manage Account > Account API Token`.
You can also create a personal token under `Profile > API Tokens`. Store the
token in an environment variable.

## Required Permissions

Use the `Read all resources` template or configure equivalent read scopes for
the resources that Cartography should ingest. The individual scopes are:

| Scope | Used for |
| --- | --- |
| Account Settings:Read | Accounts |
| Account Membership:Read | Members and roles |
| Zone:Read | Zones |
| Zone DNS:Read | DNS records |
| Workers R2 Storage:Read | R2 buckets and their custom domains |
| Workers Scripts:Read | Worker scripts |
| Workers Routes:Read | Worker routes |
| Account Rulesets:Read | Account-level rulesets and their rules |
| Zone WAF:Read | Zone-level rulesets and their rules |
| Access: Apps and Policies Read | Access applications and their attached policies |

The R2 stage degrades instead of failing the run. If the bucket listing is
refused, R2 is skipped with a warning and the Workers and ruleset stages still
run; buckets from earlier runs are left in place rather than deleted. If only the
per-bucket domain lookups are refused, the buckets are ingested with their
internet exposure (`public`, `public_domains`) left unresolved.

R2 buckets are listed once per jurisdiction (`default`, `eu` and `fedramp`), since
each jurisdiction is a separate namespace that a single listing does not cover. The
`eu` and `fedramp` jurisdictions are granted on request, so an account without the
grant answers `403` or `404` there and is treated as holding no bucket in it. Any
other error on a jurisdiction listing holds the R2 cleanup back for that run, so
buckets Cartography could not re-read are not deleted.

## Configure Cartography

Pass the token environment variable name with `--cloudflare-token-env-var`.

## Run Cartography

```bash
cartography \
  --selected-modules cloudflare \
  --cloudflare-token-env-var CLOUDFLARE_TOKEN
```

## Access applications and policies

The Access stage inventories applications once per account and reads the policies
attached to each application, including reusable policies. It creates
`CloudflareAccessApplication` and `CloudflareAccessPolicy` nodes, account
`RESOURCE` relationships, and application `HAS_POLICY` relationships.

Application graph IDs are `<account_id>/<application_id>`. A policy node represents
an attachment to one application, with ID
`<account_id>/<application_id>/<policy_id>`. The original provider IDs are retained
in `application_id` on applications and `policy_id` on policies. A policy node's
`application_id` is its account-qualified parent application ID. A reusable policy
therefore has one node per application, preserving its application-specific
`precedence` rather than overwriting another application's configuration.

Policy `include`, `require`, and `exclude` are JSON strings preserving the nested
rule blocks. An omitted or null block stays null; an empty block is stored as
`[]`. Decisions (`allow`, `deny`, `non_identity`, and `bypass`) are stored without
inferring effective protection. Application types without a DNS hostname are
supported. For public `self_hosted` applications, the stage reads public
`destinations` (or legacy `domain` and `self_hosted_domains` when destinations
are absent) and stores the validated configured values in `public_domains`.
An explicit empty or private-only destinations list overrides the legacy fields.
SaaS, bookmark, infrastructure, and private destinations are not correlated to
public DNS solely because they contain a hostname.

`CloudflareZone`-`HAS_APPLICATION` links point to the most specific known zone
in the same account for each configured public hostname. A zone association
can exist even if no matching DNS record was ingested.

`CloudflareAccessApplication`-`PROTECTS` links correlate configured hostnames to
existing, concrete, proxied A/AAAA/CNAME records owned by the same account.
Hostname matching is case-insensitive, normalizes IDNA and a trailing DNS dot,
and respects hostname label boundaries. Access wildcards match within a single
label: `*.example.com` matches `one.example.com`, but not `example.com` or
`two.one.example.com`. Partial and multi-label patterns are supported. Wildcard
DNS records are not expanded or matched to application patterns; their DNS
resolution and precedence rules differ from Access wildcard matching.

Every `PROTECTS` edge has `match_scope="configured_hostname"`. Read the
application's `public_domains` for path restrictions and its `HAS_POLICY` nodes
for decisions. A path-restricted application may have a hostname link without
protecting the entire host. These edges do not evaluate path inheritance,
overlapping application precedence, bypass policies, origin reachability, or
Cloudflare for SaaS hostname ownership. They are configuration correlations,
not effective-access verdicts. A successful resync removes obsolete DNS and
zone edges when domains or destinations change or a record becomes DNS-only.
A failed Access fetch preserves the previous application and correlation data.

See [Access application paths](https://developers.cloudflare.com/cloudflare-one/access-controls/policies/app-paths/)
and [wildcard DNS records](https://developers.cloudflare.com/dns/manage-dns-records/reference/wildcard-dns-records/)
for the different wildcard semantics.

If an application or policy API page returns HTTP 403, Access loading and
cleanup are skipped for that account, preserving its previous Access graph.
Grant the token Access application/policy read permission to enable ingestion.
Other API failures, including authentication errors, rate limits, server errors,
and connection failures, propagate so the run cannot report a successful sync
with stale Access data. A successful empty application listing removes stale Access
nodes for that account. Other accounts are cleaned independently.

API references: [applications](https://developers.cloudflare.com/api/resources/zero_trust/subresources/access/subresources/applications/methods/list/) and [application policies](https://developers.cloudflare.com/api/resources/zero_trust/subresources/access/subresources/applications/subresources/policies/methods/list/).

## Real-provider validation for Access

Use a Cloudflare test account with Zero Trust Access enabled and an active zone
you control. Arrange the following test data before starting; do not change
production Access rules or DNS records to create test cases:

- Concrete proxied DNS records and a self-hosted Access application for an exact
  hostname, including a path-restricted destination.
- A wildcard Access destination, with a matching one-level subdomain and an apex
  or deeper subdomain that must not match. A DNS-only record is a negative case.
- Multiple public destinations, preferably across two zones if available, plus
  a private-only or non-public application that must not acquire public DNS links.
- Policies with known decisions and include/require/exclude blocks. A reusable
  policy on two applications exercises attachment identity and precedence.
  A bypass example must remain visibly a bypass, not an inferred protected host.

The supported `cartography --selected-modules cloudflare` command enumerates
accounts and runs the account/member/role/zone/DNS/R2/Workers/ruleset stages as
well as Access. It does not expose an account-ID selector. Grant the read scopes
from the permission table above, including **Account Settings:Read** for account
enumeration, **Zone:Read**, **Zone DNS:Read**, and
**Access: Apps and Policies Read**, restricted to the test account and its zones.
Keep the token in a local environment variable (for example `CLOUDFLARE_TOKEN`);
never paste it into chat, source files, fixtures, or evidence.

Use a fresh disposable Neo4j database, with its URI and credentials supplied
locally. Run the existing zone and DNS stages before Access. Record the exact
Cartography revision, Python and Cloudflare SDK versions, chosen account scope,
and commands. The account-pagination issue described in [PR #2942](https://github.com/cartography-cncf/cartography/pull/2942)
and the R2 SDK compatibility issue in [PR #3425](https://github.com/cartography-cncf/cartography/pull/3425)
may affect the complete module. Verify current upstream behavior and keep
unrelated fixes separate from Access validation.

Check these results in the graph:

```cypher
MATCH (a:CloudflareAccessApplication)-[r:PROTECTS]->(d:CloudflareDNSRecord)
RETURN a.public_domains, r.match_scope, d.name, d.type, d.proxied;

MATCH (z:CloudflareZone)-[:HAS_APPLICATION]->(a:CloudflareAccessApplication)
RETURN z.name, a.public_domains;

MATCH (a:CloudflareAccessApplication)-[:HAS_POLICY]->(p:CloudflareAccessPolicy)
RETURN a.application_id, p.policy_id, p.precedence, p.decision,
       p.include, p.require, p.exclude;
```

Run a second sync to verify stable counts and updated timestamps. With the test
account owner's permission, change a test destination or proxy setting and
verify the obsolete edge disappears. Test a refused Access read with a separate
restricted token and verify prior Access nodes and edges survive. If a second
account is available, verify identical hostnames do not create cross-account links.

Before submission, retain sanitized sync logs, node/relationship counts, and
query output or screenshots showing the expected graph and negative cases.
Remove tokens, account/application/policy identifiers, private hostnames, emails,
group IDs, and other personal data, using consistent placeholders to preserve
relationships. Real provider results are still required by `CONTRIBUTING.md`;
mocked API responses and local Neo4j tests do not replace that evidence.
