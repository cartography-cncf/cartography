# Amazon Inspector

Cartography stores Amazon Inspector findings in two shapes:

- Package vulnerability findings on EC2 instances are grouped into finding sets. One
  `AWSInspectorInstanceFindings` node per instance links to one `AWSInspectorFindingSet`,
  which contains the `AWSInspectorFindingContent` nodes the instance shares with other
  instances.
- Every other finding, including network reachability findings on EC2 instances and
  findings on ECR images, repositories, and Lambda functions, is one `AWSInspectorFinding`
  node per finding ARN.

## Why EC2 package findings use finding sets

Inspector reports one finding per instance and vulnerability. Instances launched from
the same AMI report almost the same findings, so a fleet of thousands of instances stores
the same data thousands of times. Autoscaled fleets also replace instances daily, so the
sync rewrites and deletes millions of findings a day.

With finding sets, the data that is the same for many instances is stored once:

```
(:AWSAccount)-[:MEMBER]->(:AWSInspectorInstanceFindings)
(:AWSInspectorInstanceFindings)-[:AFFECTS]->(:AWSEC2Instance)
(:AWSInspectorInstanceFindings)-[:HAS_FINDINGS]->(:AWSInspectorFindingSet)
(:AWSInspectorFindingSet)-[:CONTAINS]->(:AWSInspectorFindingContent:CVE)
(:AWSInspectorFindingContent)-[:HAS]->(:AWSInspectorPackage)
(:AWSInspectorFindingContent)-[:HAS_VULNERABILITY]->(:AWSInspectorVulnerability)
(:CVEMetadata)-[:ENRICHES]->(:AWSInspectorFindingContent:CVE)
```

- An `AWSInspectorFindingContent` is everything in a finding that does not depend on the
  instance: the vulnerability, packages, Inspector score, severity, status, and fix and
  exploit availability. Instances whose network reachability changes their Inspector
  score get a different content.
- An `AWSInspectorFindingSet` is a distinct group of contents that one or more instances
  report.
- An `AWSInspectorInstanceFindings` holds what belongs to one instance: its account,
  AMI, the ID of each of its findings, and when Inspector first observed them. It exists
  even when Cartography has not synced the `AWSEC2Instance`, and links to it when it has.

When an instance is replaced, the sync adds one `AWSInspectorInstanceFindings` node and
links it to an existing set, and cleanup deletes the old instance's node. Sets and
contents change only when the findings themselves change.

## Migrate queries on EC2 package findings

Queries that read `AWSInspectorFinding` nodes for package vulnerabilities on EC2
instances must change. Queries on any other finding do not. Apply these rules in order.

1. **Reach the findings through the instance's set.** Replace the finding match:

   ```cypher
   // Before
   MATCH (f:AWSInspectorFinding {type: 'PACKAGE_VULNERABILITY'})-[a:AFFECTS]->(i:AWSEC2Instance)
   // After
   MATCH (i:AWSEC2Instance)<-[:AFFECTS]-(fi:AWSInspectorInstanceFindings)
         -[:HAS_FINDINGS]->(s:AWSInspectorFindingSet)
         -[:CONTAINS]->(f:AWSInspectorFindingContent)
   ```

   Every `AWSInspectorFindingContent` is a package vulnerability, so drop the `type`
   filter. To include instances that Cartography has not synced, start from `fi` and
   leave out the `AWSEC2Instance` match.

2. **Read finding properties from the node that now holds them.**

   | Property on `AWSInspectorFinding` | Read it from |
   |---|---|
   | `name`, `type`, `status`, `severity`, `cvssscore`, `cvssvector`, `vulnerabilityid`, `cve_id`, `vendorseverity`, `vulnerablepackageids`, `fixavailable`, `exploitavailable`, `lastknownexploitat`, `epss_score_inspector` | `f`, the `AWSInspectorFindingContent` |
   | `description`, `referenceurls`, `relatedvulnerabilities`, `vendorcvssvectors`, `vendorcvssscores`, `source`, `sourceurl`, `vendorcreatedat`, `vendorupdatedat` | the `AWSInspectorVulnerability`: `(f)-[:HAS_VULNERABILITY]->(v)` |
   | `instanceid`, `awsaccount`, `region` | `fi` |
   | `firstobservedat` | the first-observed expression in rule 4 |
   | `updatedat` | `fi.last_observed_at`, the latest update across the instance's findings |
   | `id`, `arn` | the ARN expression in rule 5 |

3. **Keep package joins on the content.** `(f)-[:HAS]->(p:AWSInspectorPackage)` and its
   relationship properties, such as `fixedinversion` and `remediation`, are unchanged
   with `f` bound to the content.

4. **Compute first-observed time per finding.** Most of an instance's findings share the
   time Inspector first scanned it. Findings first observed more than an hour later are
   listed separately:

   ```cypher
   WITH fi, f, s, [k IN range(0, size(fi.late_content_ids) - 1) WHERE fi.late_content_ids[k] = f.id] AS late
   WITH fi, f, s,
        CASE WHEN size(late) > 0 THEN fi.late_first_observed_at[late[0]] ELSE fi.first_observed_at END
        AS first_observed_at
   ```

   This replaces both the finding's `firstobservedat` and the `firstseen` of its
   `AFFECTS` relationship. The `AFFECTS.firstseen` value restarted whenever Cartography
   recreated a finding node, so the Inspector time is the better basis for SLAs.

5. **Build the finding ARN from the instance's finding IDs.** `fi.finding_ids` lists the
   instance's finding IDs in the order of `s.content_ids`:

   ```cypher
   WITH fi, f, s, [k IN range(0, size(s.content_ids) - 1) WHERE s.content_ids[k] = f.id][0] AS position
   RETURN 'arn:aws:inspector2:' + fi.region + ':' + fi.awsaccount + ':finding/' + fi.finding_ids[position] AS arn
   ```

   To find the instance that has a given finding ARN, take the finding ID after
   `finding/` and match `fi` where `$finding_id IN fi.finding_ids`. Add the account or
   region from the ARN to narrow the scan.

6. **Use the instance's sync time for the scan time.** `AFFECTS.lastupdated` becomes
   `fi.lastupdated`.

7. **Count findings as (instance, content) rows.** A content node can stand for many
   instances, so count `fi` and `f` pairs, not content nodes.

8. **Enrich through the content.** `CVEMetadata` now enriches each content node through
   the `:CVE` label, so `(m:CVEMetadata)-[:ENRICHES]->(f)` works with `f` bound to the
   content.

### Example: a remediation SLA report

```cypher
// Before
MATCH (i:AWSEC2Instance {id: $instance_id})
MATCH (f:AWSInspectorFinding {type: 'PACKAGE_VULNERABILITY', status: 'ACTIVE'})-[a:AFFECTS]->(i)
OPTIONAL MATCH (f)-[h:HAS]->(:AWSInspectorPackage)
RETURN f.vulnerabilityid AS cve_id, f.severity AS severity, f.description AS description,
       f.arn AS finding_arn, h.fixedinversion AS fixed_version,
       a.firstseen / 1000 AS first_seen, a.lastupdated AS scan_completed_at

// After
MATCH (i:AWSEC2Instance {id: $instance_id})<-[:AFFECTS]-(fi:AWSInspectorInstanceFindings)
      -[:HAS_FINDINGS]->(s:AWSInspectorFindingSet)
      -[:CONTAINS]->(f:AWSInspectorFindingContent {status: 'ACTIVE'})
MATCH (f)-[:HAS_VULNERABILITY]->(v:AWSInspectorVulnerability)
OPTIONAL MATCH (f)-[h:HAS]->(:AWSInspectorPackage)
WITH fi, f, s, v, h,
     [k IN range(0, size(fi.late_content_ids) - 1) WHERE fi.late_content_ids[k] = f.id] AS late,
     [k IN range(0, size(s.content_ids) - 1) WHERE s.content_ids[k] = f.id][0] AS position
RETURN f.vulnerabilityid AS cve_id, f.severity AS severity, v.description AS description,
       'arn:aws:inspector2:' + fi.region + ':' + fi.awsaccount + ':finding/' + fi.finding_ids[position]
           AS finding_arn,
       h.fixedinversion AS fixed_version,
       CASE WHEN size(late) > 0 THEN fi.late_first_observed_at[late[0]] ELSE fi.first_observed_at END
           .epochSeconds AS first_seen,
       fi.lastupdated AS scan_completed_at
```

### Upgrading an existing graph

The first sync after upgrading loads EC2 package findings as finding sets and its
cleanup deletes the `AWSInspectorFinding` nodes that held them before. On a large fleet,
that first cleanup deletes as many nodes as the fleet had findings, so it takes about as
long as a cleanup after a day of full churn did before. Later syncs only delete the
nodes of replaced instances.
