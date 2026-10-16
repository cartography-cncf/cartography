## AWS Tagging and Labels

This guide describes two conventions that affect AWS queries across the graph:
dynamic tag relationships and provider-prefixed resource labels.

### Dynamic AWS tags

An `AWSTag` is identified by `{key}:{value}` and is connected from a resource
with `TAGGED`:

```cypher
(resource)-[:TAGGED]->(:AWSTag)
```

Tag relationships are loaded centrally from the AWS Resource Groups Tagging
API. They are dynamic relationships rather than relationships declared in each
resource's model schema. A shared declarative catalog drives both runtime
matching and generated schema documentation so the supported relationships
remain consistent.

Because the id is only `{key}:{value}`, one `AWSTag` node is shared by every
account whose resources carry that tag. Each `TAGGED` relationship records the
account that owns it, so an account's sync only removes its own stale `TAGGED`
relationships.

A tag on a resource that is not in the graph is still loaded, but it has no
`TAGGED` relationship. Once every account has synced, a single sweep removes
every `AWSTag` node that no relationship uses, except tags stamped by a newer
sync running against the same graph. It runs in batches of
`aws_tagging_api_cleanup_batch`. The sweep is skipped if any
account fails, so it never removes tags that the failed account would have
linked. Callers that run `_sync_one_account()` for each account themselves must
call `cartography.intel.aws.resourcegroupstaggingapi.cleanup_orphan_tags()`
after their account loop.

The authoritative mapping is `AWS_TAGGABLE_RESOURCES` in
`cartography/models/aws_tagging.py`. The current supported source labels are:

- Compute and networking: `AWSAutoScalingGroup`, `AWSEC2Instance`,
  `AWSEC2KeyPair`, `AWSEC2SecurityGroup`, `AWSEC2Subnet`,
  `AWSElasticIPAddress`, `AWSInternetGateway`, `AWSLambda`,
  `AWSLoadBalancer`, `AWSLoadBalancerV2`, `AWSNetworkInterface`,
  `AWSTransitGateway`, `AWSTransitGatewayAttachment`, and `AWSVpc`.
- Containers: `AWSECRRepository`, `AWSECSCluster`, `AWSECSContainer`,
  `AWSECSContainerInstance`, `AWSECSTask`, `AWSECSTaskDefinition`, and
  `AWSEKSCluster`.
- Data and storage: `AWSDBSubnetGroup`, `AWSDynamoDBTable`, `AWSEBSVolume`,
  `AWSElasticacheCluster`, `AWSEMRCluster`, `AWSESDomain`,
  `AWSRDSCluster`, `AWSRDSInstance`, `AWSRDSSnapshot`,
  `AWSRedshiftCluster`, and `AWSS3Bucket`.
- Identity, security, and messaging: `AWSKMSKey`, `AWSRole`,
  `AWSSecretsManagerSecret`, `AWSSQSQueue`, and `AWSUser`.

Because support follows the runtime mapping, check that mapping when exact
coverage matters.

Find resources with a tag:

```cypher
MATCH (resource)-[:TAGGED]->(:AWSTag {key: $key, value: $value})
RETURN labels(resource) AS labels, resource.id, resource.arn, resource.name
ORDER BY resource.name
```

Find resources missing a required tag:

```cypher
MATCH (account:AWSAccount)-[:RESOURCE]->(resource)
WHERE resource.lastupdated IS NOT NULL
  AND NOT EXISTS {
    MATCH (resource)-[:TAGGED]->(:AWSTag {key: $required_key})
  }
RETURN account.id, labels(resource), resource.id, resource.arn, resource.name
ORDER BY account.id, resource.name
```

Narrow the second query to the resource labels relevant to your policy. Not
every AWS node type is discoverable through the Resource Groups Tagging API.

### Provider-prefixed labels

AWS resource labels are provider-prefixed. New queries should use documented
`AWS*` labels such as `AWSLoadBalancer`, `AWSIpRange`, and
`AWSIpPermissionInbound`.

Historically unprefixed labels remain attached as compatibility aliases until
v1.0.0. They preserve existing queries during migration, but they are not the
preferred provider-specific interface. Some unprefixed labels are also
intentional ontology labels used for cross-platform queries, so do not assume
that every unprefixed label is deprecated.

Use the provider-prefixed label when the query depends on AWS-specific
properties or relationships:

```cypher
MATCH (load_balancer:AWSLoadBalancer)
RETURN load_balancer.id, load_balancer.region
```

Use an ontology label when the query intentionally spans providers:

```cypher
MATCH (load_balancer:LoadBalancer)
RETURN labels(load_balancer), load_balancer.id
```

During the compatibility period, avoid creating new queries that depend only
on a historical unprefixed provider label. This keeps queries valid when those
aliases are removed.
