# Scaleway

```{toctree}
config
schema
```

The Scaleway module ingests identity and access management, compute, container,
database, DNS, Kubernetes, networking, secret, serverless, and storage resources
from a Scaleway organization.

## IAM access materialization

Scaleway IAM policies apply to users, applications, or groups. Their rules grant
named permission sets within a project or across the organization. Cartography
materializes these grants as `HAS_ROLE` relationships from principals to
permission sets and `CAN_ACCESS` relationships from principals to projects.

Organization-scoped rules create `CAN_ACCESS` relationships to every project in
the organization. The relationship property `has_condition` indicates that
every grant path to the project is gated by an IAM rule condition. Resources
connect to projects through `RESOURCE`, allowing access-path analysis to
continue from a principal through its accessible projects.
