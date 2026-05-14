# Multiple intel modules modifying the same node type

It is allowed (and encouraged) for more than one intel module to write to the same node label. There are two distinct patterns depending on whether the second module brings additional properties.

## Simple relationship pattern

Use this when module A only refers to module B's nodes by **ID**, with no extra properties about B.

When A loads, the relationship schema's `MATCH` finds and connects to existing B nodes.

Example: an RDS instance refers to EC2 security groups by ID. The RDS API doesn't add any properties to security groups beyond their IDs.

```python
@dataclass(frozen=True)
class RDSInstanceToSecurityGroupRel(CartographyRelSchema):
    target_node_label: str = "EC2SecurityGroup"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher({
        "id": PropertyRef("SecurityGroupId"),  # ID only
    })
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "MEMBER_OF_EC2_SECURITY_GROUP"
    properties: RDSInstanceToSecurityGroupRelProperties = RDSInstanceToSecurityGroupRelProperties()
```

## Composite node pattern

Use this when module A refers to module B's nodes **and** provides additional properties about them. Define a second node schema named `<B>ASchema` (a "B" object as known by an "A" object). Both schemas target the same node label, so `load()` performs a `MERGE` that combines properties.

Example: in AWS EC2 we have `EBSVolumeSchema` (from the EBS API) and `EBSVolumeInstanceSchema` (from the EC2 Instance API). The EC2 Instance API exposes `deleteontermination`, which the EBS API does not.

```python
@dataclass(frozen=True)
class EBSVolumeInstanceProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("VolumeId")
    arn: PropertyRef = PropertyRef("Arn", extra_index=True)
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    deleteontermination: PropertyRef = PropertyRef("DeleteOnTermination")  # additional


@dataclass(frozen=True)
class EBSVolumeInstanceSchema(CartographyNodeSchema):
    label: str = "EBSVolume"  # same label as EBSVolumeSchema
    properties: EBSVolumeInstanceProperties = EBSVolumeInstanceProperties()
    sub_resource_relationship: EBSVolumeToAWSAccountRel = EBSVolumeToAWSAccountRel()
    # ... other relationships
```

## Choosing the pattern

Question to ask: **does the referring module provide additional properties about the target?**

- No -> simple relationship pattern.
- Yes -> composite node pattern.

## Common sync patterns

### Pattern 1 — simple service with users (LastPass-style)

Single main entity, simple tenant relationship, standard fields (`id`, `email`, `created_at`).

### Pattern 2 — complex infrastructure (AWS EC2-style)

Multiple entity types, complex relationships between entities, regional / account-scoped resources, multiple `load()` calls.

### Pattern 3 — hierarchical resources (route tables-style)

```python
{
    "RouteTableId": "rtb-123",
    "Associations": [{"SubnetId": "subnet-abc"}, {"SubnetId": "subnet-def"}],
}
# transform()
{
    "id": "rtb-123",
    "subnet_ids": ["subnet-abc", "subnet-def"],  # flattened for one_to_many=True
}
```
