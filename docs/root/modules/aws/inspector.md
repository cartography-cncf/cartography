# Amazon Inspector

Cartography stores Amazon Inspector findings in two shapes:

- Cartography groups package vulnerability findings on EC2 instances into finding sets.
  One `AWSInspectorInstanceFindings` node per instance points at one `AWSInspectorFindingSet`,
  which contains the `AWSInspectorFindingContent` nodes the instance shares with other
  instances.
- Every other finding, including network reachability findings on EC2 instances and
  findings on ECR images, repositories, and Lambda functions, is one `AWSInspectorFinding`
  node per finding ARN.

Earlier versions stored every finding as an `AWSInspectorFinding`. To update queries
written for that shape, see [Migrate queries on EC2 package findings](#migrate-queries-on-ec2-package-findings).

## Vulnerabilities and CVEs

Each package vulnerability that Inspector reports is one `AWSInspectorVulnerability`
node. It holds the advisory data that is the same for every finding of the vulnerability:
the description, reference URLs, and the vendor and NVD CVSS entries.

```cypher
(:AWSInspectorFinding)-[:HAS_VULNERABILITY]->(:AWSInspectorVulnerability)
(:AWSInspectorFindingContent)-[:HAS_VULNERABILITY]->(:AWSInspectorVulnerability)
(:CVEMetadata)-[:ENRICHES]->(:AWSInspectorVulnerability:CVE)
```

Cartography labels a vulnerability `:CVE` only when its identifier is a CVE. Inspector
also reports GHSA and ALAS advisories; those vulnerabilities have no `cve_id` and no
`:CVE` label. Findings don't carry `:CVE`, so a query on `:CVE` returns each Inspector CVE
once rather than once per affected resource. The first sync after upgrading removes the
`:CVE` label and its `_ont_*` fields from findings that earlier versions labeled.

## Packages

Each vulnerable package that Inspector reports is one `AWSInspectorPackage` node. Its
ID starts with Inspector's package manager and, for an operating system package, the
distribution, such as `OS|amazon|openssl|1:1.0.2k-24.amzn2.X86_64` or
`PIP|requests|2.28.0`. Packages from different ecosystems or distributions never share a
node. The same build on two releases of one distribution, such as Debian 11 and 12,
shares one, as it shares one `PackageVersion`.

When Cartography recognizes the package manager, the package also gets a package URL in
`purl`. An operating system package needs the platform of the affected EC2 instance or
ECR image, such as `AMAZON_LINUX_2023` or `DEBIAN_12`, to name its distribution. The
ontology packages sync maps each package with a package URL to a `PackageVersion`, the
same node that Trivy, Syft, and other scanners report the package as:

```cypher
(:PackageVersion)-[:DETECTED_AS]->(:AWSInspectorPackage)
```

To find the package versions a finding affects, follow its packages:

```cypher
MATCH (f:AWSInspectorFindingContent)-[:HAS]->(:AWSInspectorPackage)
      <-[:DETECTED_AS]-(pv:PackageVersion)
RETURN f.vulnerabilityid, pv.id
```

## Why EC2 package findings use finding sets

Inspector reports one finding per instance and vulnerability. Instances launched from
the same AMI report almost the same findings, so a fleet of thousands of instances stores
the same data thousands of times. Autoscaled fleets also replace instances daily, so the
sync writes and deletes millions of findings a day.

With finding sets, Cartography stores the data that many instances share once:

```cypher
(:AWSAccount)-[:MEMBER]->(:AWSInspectorInstanceFindings)
(:AWSInspectorInstanceFindings)-[:AFFECTS]->(:AWSEC2Instance)
(:AWSInspectorInstanceFindings)-[:HAS_FINDING_SET]->(:AWSInspectorFindingSet)
(:AWSInspectorFindingSet)-[:CONTAINS]->(:AWSInspectorFindingContent)
(:AWSInspectorFindingContent)-[:HAS]->(:AWSInspectorPackage)
(:AWSInspectorFindingContent)-[:HAS_VULNERABILITY]->(:AWSInspectorVulnerability)
```

- An `AWSInspectorFindingContent` is everything in a finding that does not depend on the
  instance: the vulnerability, packages, Inspector score, severity, status, and fix and
  exploit availability. Instances whose network reachability changes their Inspector
  score get a different content.
- An `AWSInspectorFindingSet` is a distinct group of contents that one or more instances
  report. Each content has one or more slots in the set, one per finding that reports it.
  The `CONTAINS` relationship lists them in `slots`.
- An `AWSInspectorInstanceFindings` holds the instance's account, AMI, and region. It
  exists even when Cartography has not synced the `AWSEC2Instance`, and links to it when
  it has.
- The `HAS_FINDING_SET` relationship holds the instance's own findings as lists that line
  up with the set's slots. Entry `k` of `finding_ids`, `first_observed_at_ms`,
  `last_observed_at_ms`, and `updated_at_ms` belongs to slot `k`. The times are
  Inspector's own, in epoch milliseconds.

When a fleet replaces an instance, the sync adds one `AWSInspectorInstanceFindings` node and
links it to a set that usually exists already, and cleanup deletes the old instance's
node. Sets and contents change only when the findings themselves change.

### Read one row per finding

This query returns one row per instance and finding, with the finding's ARN and times:

```cypher
MATCH (fi:AWSInspectorInstanceFindings)-[o:HAS_FINDING_SET]->(s:AWSInspectorFindingSet)
WHERE s.id = fi.finding_set_id
MATCH (s)-[c:CONTAINS]->(f:AWSInspectorFindingContent)
UNWIND c.slots AS k
RETURN fi.instanceid AS instance, f.vulnerabilityid AS vulnerability,
       o.finding_arn_prefix + o.finding_ids[k] AS finding_arn,
       datetime({epochMillis: o.first_observed_at_ms[k]}) AS first_observed_at
```

Keep the `s.id = fi.finding_set_id` condition. When an instance's findings change, it
moves to another set. Until cleanup runs, the instance also keeps its previous
`HAS_FINDING_SET` relationship, which still holds the findings that set had.

## Migrate queries on EC2 package findings

Queries that read `AWSInspectorFinding` nodes for package vulnerabilities on EC2
instances must change. Queries on any other finding do not. Apply these rules in order.

1. **Reach the findings through the instance's set.** Replace the finding match:

   ```cypher
   // Before
   MATCH (f:AWSInspectorFinding {type: 'PACKAGE_VULNERABILITY'})-[a:AFFECTS]->(i:AWSEC2Instance)
   // After
   MATCH (i:AWSEC2Instance)<-[:AFFECTS]-(fi:AWSInspectorInstanceFindings)
         -[o:HAS_FINDING_SET]->(s:AWSInspectorFindingSet)
   WHERE s.id = fi.finding_set_id
   MATCH (s)-[c:CONTAINS]->(f:AWSInspectorFindingContent)
   UNWIND c.slots AS k
   ```

   Every `AWSInspectorFindingContent` is a package vulnerability, so drop the `type`
   filter. To include instances that Cartography has not synced, start from `fi` and
   leave out the `AWSEC2Instance` match.

2. **Read finding properties from where they are now.**

   | Property on `AWSInspectorFinding` | Read it from |
   |---|---|
   | `name`, `type`, `status`, `severity`, `cvssscore`, `cvssvector`, `vulnerabilityid`, `cve_id`, `vendorseverity`, `vulnerablepackageids`, `fixavailable`, `exploitavailable`, `lastknownexploitat`, `epss_score_inspector` | `f`, the `AWSInspectorFindingContent` |
   | `instanceid`, `awsaccount`, `region` | `fi` |
   | `id`, `arn` | `o.finding_arn_prefix + o.finding_ids[k]` |
   | `firstobservedat` | `o.first_observed_at_ms[k]`, in epoch milliseconds |
   | `updatedat` | `o.updated_at_ms[k]`, in epoch milliseconds |

   Advisory data such as `description` and `referenceurls` stays on the
   `AWSInspectorVulnerability`: `(f)-[:HAS_VULNERABILITY]->(v)`.

3. **Keep package joins on the content.** `(f)-[:HAS]->(p:AWSInspectorPackage)` and its
   relationship properties, such as `fixedinversion` and `remediation`, are unchanged
   with `f` bound to the content.

4. **Use Inspector's first-observed time for SLAs.** `o.first_observed_at_ms[k]` replaces
   the `firstseen` of the finding's `AFFECTS` relationship. `AFFECTS.firstseen` recorded
   when Cartography created the relationship and restarted whenever the finding node was
   recreated. Inspector's time does not restart, but it can be earlier than the
   Cartography time it replaces, so compare both on a test graph before you switch an
   SLA report.

5. **Find a finding by ARN.** Take the finding ID after `finding/` and match it on the
   current set's relationship. Add the account or region from the ARN to narrow the scan.

   ```cypher
   MATCH (fi:AWSInspectorInstanceFindings)-[o:HAS_FINDING_SET]->(s:AWSInspectorFindingSet)
   WHERE s.id = fi.finding_set_id AND $finding_id IN o.finding_ids
   RETURN fi
   ```

6. **Use the instance's sync time for the scan time.** `AFFECTS.lastupdated` becomes
   `fi.lastupdated`.

7. **Count findings as rows after `UNWIND c.slots`.** A content node can stand for many
   instances and many slots, so count rows, not content nodes.

8. **Write your own per-finding properties to a node you own.** A property set on a
   content node applies to every instance and slot that shares the content, and a sync
   that changes the content leaves it behind. Write data that depends only on the
   vulnerability and package to the content, and reapply it after each sync. Key data
   that depends on the instance by finding ARN on a node that you create.

### Example: a remediation SLA report

```cypher
// Before
MATCH (i:AWSEC2Instance {id: $instance_id})
MATCH (f:AWSInspectorFinding {type: 'PACKAGE_VULNERABILITY', status: 'ACTIVE'})-[a:AFFECTS]->(i)
OPTIONAL MATCH (f)-[h:HAS]->(:AWSInspectorPackage)
RETURN f.vulnerabilityid AS vulnerability, f.severity AS severity,
       f.description AS description, f.arn AS finding_arn,
       collect(h.fixedinversion) AS fixed_versions, a.firstseen AS first_seen_ms

// After
MATCH (i:AWSEC2Instance {id: $instance_id})<-[:AFFECTS]-(fi:AWSInspectorInstanceFindings)
      -[o:HAS_FINDING_SET]->(s:AWSInspectorFindingSet)
WHERE s.id = fi.finding_set_id
MATCH (s)-[c:CONTAINS]->(f:AWSInspectorFindingContent {status: 'ACTIVE'})
      -[:HAS_VULNERABILITY]->(v:AWSInspectorVulnerability)
UNWIND c.slots AS k
OPTIONAL MATCH (f)-[h:HAS]->(:AWSInspectorPackage)
RETURN f.vulnerabilityid AS vulnerability, f.severity AS severity,
       v.description AS description,
       o.finding_arn_prefix + o.finding_ids[k] AS finding_arn,
       collect(h.fixedinversion) AS fixed_versions,
       o.first_observed_at_ms[k] AS first_seen_ms
```

### Example: CVEs on the nodes of each EKS cluster

Instances that share a set share its findings, so this query groups nodes by set before
it expands the findings:

```cypher
MATCH (eks:AWSEKSCluster)-[:MAPS_TO]->(:KubernetesCluster)-[:RESOURCE]->(n:KubernetesNode)
      -[:IS_INSTANCE]->(:AWSEC2Instance)<-[:AFFECTS]-(fi:AWSInspectorInstanceFindings)
      -[:HAS_FINDING_SET]->(s:AWSInspectorFindingSet)
WHERE s.id = fi.finding_set_id
OPTIONAL MATCH (p:KubernetesPod {status_phase: 'Running'})-[:RUNS_ON]->(n)
WITH eks, s, n, count(DISTINCT p) AS pods
WITH eks, s, count(n) AS nodes, sum(pods) AS pods
MATCH (s)-[:CONTAINS]->(f:AWSInspectorFindingContent {status: 'ACTIVE'})
      -[:HAS_VULNERABILITY]->(v:AWSInspectorVulnerability:CVE)
WITH eks, s, v, nodes, pods,
     max(CASE f.severity WHEN 'CRITICAL' THEN 4 WHEN 'HIGH' THEN 3
                         WHEN 'MEDIUM' THEN 2 WHEN 'LOW' THEN 1 ELSE 0 END) AS severity
RETURN eks.arn AS cluster, eks.name AS cluster_name, v.cve_id AS cve,
       max(severity) AS severity, sum(nodes) AS affected_nodes,
       sum(pods) AS running_pods
ORDER BY cluster, severity DESC, running_pods DESC
```

## Upgrade an existing graph

The first sync after upgrading loads EC2 package findings as finding sets, and its
cleanup deletes the `AWSInspectorFinding` nodes that held them before. On a large fleet,
that first cleanup deletes as many nodes as the fleet had findings, so it takes about as
long as a cleanup after a day of full churn did before. Later syncs only delete the nodes
of replaced instances.
