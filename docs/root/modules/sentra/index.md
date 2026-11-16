# Sentra

```{toctree}
config
schema
```

Cartography ingests data security posture from [Sentra](https://www.sentra.io/):
the data stores Sentra discovered, the data classes it found in them, and its
active alerts. The organization and alerts use the `Tenant` and `SecurityIssue`
ontology labels.

Each data store links with `CONTAINS` to the data classes Sentra found in it,
so a query can find every store that holds, for example, credentials or payment
card numbers.

A data store links with `MONITORS` to the AWS resource it is, when Cartography
has synced that resource and Sentra's identifier proves which resource it is:

| Target | Matched on |
|---|---|
| `AWSS3Bucket` | The bucket name, from an S3 ARN or from the name of an `s3` store in an AWS account |
| `AWSRDSInstance` | The DB instance ARN |
| `AWSRDSCluster` | The DB cluster ARN |
| `AWSDynamoDBTable` | The table ARN |
| `AWSRedshiftCluster` | The cluster ARN |

Data stores in other clouds and SaaS applications are ingested without a link to
the provider resource.

Cartography ingests alerts whose status is `pending`, `opened`, or
`in_progress`. After each sync, cleanup removes the alerts that Sentra resolved
or ignored since the previous sync. An alert links with `AFFECTS` to the
`SentraDataStore` it was raised on, or to the `AWSRole` it was raised on when
Sentra reports the role ARN.
