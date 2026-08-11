# Cartography Schema

Each module documents its own node labels, properties and relationships. Most pages are
generated from Cartography's declarative data model; a few legacy modules still ship a
hand-written page.

## Quick notes on notation

- Relationships are written as Cypher patterns, for example
  `(:AWSAccount)-[:RESOURCE]->(:AWSEC2Instance)`.

- A property marked `Yes` in the `Index` column is indexed, so queries filtering on it
  run faster.

- On the remaining hand-written pages, indexed fields are bolded instead, and a more
  specific node may be written `GenericNode::SpecificNode`. For example a `RaceCar` node
  that also carries the `Car` label is written `Car::RaceCar`.

## Schema by module

Every module schema page is reachable through its own module index except for the internal
Cartography metadata schema, which is attached here to keep it out of the orphan list.

```{toctree}
:hidden:

../modules/_cartography-metadata/schema
```

- [Cartography Metadata](../modules/_cartography-metadata/schema.md)
- [AIBOM](../modules/aibom/schema.md)
- [Airbyte](../modules/airbyte/schema.md)
- [Anthropic](../modules/anthropic/schema.md)
- [AWS](../modules/aws/schema.md)
- [Azure](../modules/azure/schema.md)
- [BBOT](../modules/bbot/schema.md)
- [Bigfix](../modules/bigfix/schema.md)
- [Circleci](../modules/circleci/schema.md)
- [Cloudflare](../modules/cloudflare/schema.md)
- [Crowdstrike](../modules/crowdstrike/schema.md)
- [Cve](../modules/cve/schema.md)
- [Cve Metadata](../modules/cve_metadata/schema.md)
- [Databricks](../modules/databricks/schema.md)
- [Digitalocean](../modules/digitalocean/schema.md)
- [Docker Scout](../modules/docker_scout/schema.md)
- [Duo](../modules/duo/schema.md)
- [GCP](../modules/gcp/schema.md)
- [Github](../modules/github/schema.md)
- [Gitlab](../modules/gitlab/schema.md)
- [Googleworkspace](../modules/googleworkspace/schema.md)
- [Gsuite](../modules/gsuite/schema.md)
- [Jamf](../modules/jamf/schema.md)
- [Jumpcloud](../modules/jumpcloud/schema.md)
- [Kandji](../modules/kandji/schema.md)
- [Keycloak](../modules/keycloak/schema.md)
- [Kubernetes](../modules/kubernetes/schema.md)
- [Lastpass](../modules/lastpass/schema.md)
- [Microsoft](../modules/microsoft/schema.md)
- [Modal](../modules/modal/schema.md)
- [Netlify](../modules/netlify/schema.md)
- [Oci](../modules/oci/schema.md)
- [Okta](../modules/okta/schema.md)
- [Ontology](../modules/ontology/schema.md)
- [Openai](../modules/openai/schema.md)
- [Pagerduty](../modules/pagerduty/schema.md)
- [Railway](../modules/railway/schema.md)
- [Salesforce](../modules/salesforce/schema.md)
- [Scaleway](../modules/scaleway/schema.md)
- [Semgrep](../modules/semgrep/schema.md)
- [SentinelOne](../modules/sentinelone/schema.md)
- [Sentry](../modules/sentry/schema.md)
- [Slack](../modules/slack/schema.md)
- [Snipeit](../modules/snipeit/schema.md)
- [Snowflake](../modules/snowflake/schema.md)
- [Socket.dev](../modules/socketdev/schema.md)
- [Spacelift](../modules/spacelift/schema.md)
- [Subimage](../modules/subimage/schema.md)
- [Supabase](../modules/supabase/schema.md)
- [Syft](../modules/syft/schema.md)
- [Tailscale](../modules/tailscale/schema.md)
- [Tenable](../modules/tenable/schema.md)
- [Trivy](../modules/trivy/schema.md)
- [Ubuntu](../modules/ubuntu/schema.md)
- [Vercel](../modules/vercel/schema.md)
- [Wiz](../modules/wiz/schema.md)
- [Workday](../modules/workday/schema.md)
- [Workos](../modules/workos/schema.md)
