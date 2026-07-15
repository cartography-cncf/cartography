## AWS Infrastructure Investigations

This guide collects graph patterns for investigating AWS networking, regional
security coverage, EKS certificate metadata, and EC2 instance age. Refer to the
[AWS schema reference](schema.md) for complete node properties.

### VPC CIDR blocks and peering

`AWSCidrBlock` is the base label for `AWSIpv4CidrBlock` and
`AWSIpv6CidrBlock`. A VPC is connected to each associated block through
`BLOCK_ASSOCIATION`. VPC peering connections identify both the requester and
accepter VPCs and CIDR blocks.

```cypher
(:AWSVpc)-[:BLOCK_ASSOCIATION]->(:AWSCidrBlock)
(:AWSPeeringConnection)-[:REQUESTER_CIDR]->(:AWSCidrBlock)
(:AWSPeeringConnection)-[:ACCEPTER_CIDR]->(:AWSCidrBlock)
```

Show account-to-account peering at a high level:

```cypher
MATCH path =
  (:AWSAccount)-[:RESOURCE|BLOCK_ASSOCIATION*..]->(:AWSCidrBlock)
  <-[:ACCEPTER_CIDR]-(:AWSPeeringConnection)-[:REQUESTER_CIDR]->
  (:AWSCidrBlock)<-[:RESOURCE|BLOCK_ASSOCIATION*..]-(:AWSAccount)
RETURN path
```

Investigate inbound security-group rules reachable across a peering
connection:

```cypher
MATCH (outbound_account:AWSAccount)
      -[:RESOURCE|BLOCK_ASSOCIATION*..]->(:AWSCidrBlock)
      <-[:ACCEPTER_CIDR]-(:AWSPeeringConnection)-[:REQUESTER_CIDR]->
      (inbound_block:AWSCidrBlock)<-[:BLOCK_ASSOCIATION]-
      (inbound_vpc:AWSVpc)<-[:RESOURCE]-(inbound_account:AWSAccount)
MATCH (inbound_range:IpRange {id: inbound_block.cidr_block})
      -[:MEMBER_OF_IP_RULE]->(inbound_rule:IpPermissionInbound)
      -[:MEMBER_OF_EC2_SECURITY_GROUP]->(inbound_group:AWSEC2SecurityGroup)
      <-[:MEMBER_OF_EC2_SECURITY_GROUP]-(inbound_vpc)
RETURN outbound_account.name, inbound_account.name, inbound_range.range,
       inbound_rule.fromport, inbound_rule.toport, inbound_rule.protocol,
       inbound_group.name, inbound_vpc.id
```

The second query shows configured reachability, not observed traffic. Route
tables, network ACLs, and application behavior can impose additional
constraints.

### GuardDuty regional coverage

GuardDuty detectors are regional. Coverage checks therefore need to match
resources and enabled detectors by both account and region.

List enabled regions:

```cypher
MATCH (account:AWSAccount)-[:RESOURCE]->(detector:AWSGuardDutyDetector)
WHERE detector.status = "ENABLED"
RETURN DISTINCT account.name, detector.region
ORDER BY account.name, detector.region
```

Find EC2 instances without an enabled detector in the same account and region:

```cypher
MATCH (account:AWSAccount)-[:RESOURCE]->(instance:AWSEC2Instance)
WHERE NOT EXISTS {
  MATCH (account)-[:RESOURCE]->(detector:AWSGuardDutyDetector {status: "ENABLED"})
  WHERE detector.region = instance.region
}
RETURN account.name, instance.instanceid, instance.region
ORDER BY account.name, instance.region, instance.instanceid
```

This tests detector presence and status. It does not assert that every optional
GuardDuty protection plan is enabled.

### EKS certificate diagnostics

`AWSEKSCluster` records whether certificate authority data was returned and
whether Cartography could parse it. Parsed certificates expose the SHA256
fingerprint, subject, issuer, validity interval, Subject Key Identifier, and
Authority Key Identifier. Missing certificate extensions remain `null`; they
are not synthesized from the public key.

Compare certificate authorities across clusters:

```cypher
MATCH (account:AWSAccount)-[:RESOURCE]->(cluster:AWSEKSCluster)
RETURN account.id, cluster.name, cluster.region, cluster.endpoint,
       cluster.certificate_authority_sha256_fingerprint,
       cluster.certificate_authority_subject,
       cluster.certificate_authority_issuer,
       cluster.certificate_authority_subject_key_identifier,
       cluster.certificate_authority_authority_key_identifier
ORDER BY account.id, cluster.region, cluster.name
```

Identify missing or invalid certificate authority data:

```cypher
MATCH (:AWSAccount)-[:RESOURCE]->(cluster:AWSEKSCluster)
WHERE cluster.certificate_authority_parse_status <> "parsed"
RETURN cluster.name, cluster.arn, cluster.status,
       cluster.certificate_authority_parse_status,
       cluster.certificate_authority_parse_error
ORDER BY cluster.certificate_authority_parse_status, cluster.name
```

### EC2 original launch time

`AWSEC2Instance.launchtime` reports the latest launch, so it changes after a
stop and restart. The primary network interface (`device_index = 0`) is created
with the instance and cannot be detached. Its `attach_time` is therefore the
best available value for the original launch time.

```cypher
MATCH (instance:AWSEC2Instance)-[:NETWORK_INTERFACE]->
      (interface:AWSNetworkInterface {device_index: 0})
WHERE interface.attach_time IS NOT NULL
RETURN instance.instanceid,
       instance.launchtime AS latest_launch,
       interface.attach_time AS original_launch
ORDER BY original_launch
```

Do not use a secondary interface for this purpose. Its attachment time only
indicates when that interface was attached.
