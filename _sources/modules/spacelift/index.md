# Spacelift

The Spacelift module ingests:

- Accounts
- Spaces
- Infrastructure-as-code stacks
- Deployment runs
- Git commits associated with runs
- Human and system users that trigger runs
- Worker pools and their workers
- Optional CloudTrail events that link runs to EC2 instances

See [configuration](config.md) for API authentication and optional EC2
ownership tracking, and the generated [schema](schema.md) for fields and
relationships.

```{toctree}
config
schema
```
