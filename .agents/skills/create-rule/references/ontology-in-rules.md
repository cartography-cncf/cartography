# Using the ontology in rules

The ontology system adds semantic labels (`UserAccount`, `Tenant`, `Database`, `ObjectStorage`, `FileStorage`, ...) and prefixed properties (`_ont_*`, `_ont_source`) to source nodes during ingestion. Rule queries can leverage these for cross-module detection without referencing every provider-specific label.

## Example — accounts not linked to a User identity

```python
_unmanaged_accounts = Fact(
    id="unmanaged-accounts-ontology",
    name="User Accounts Not Linked to Identity",
    description="Detects user accounts without a corresponding User identity",
    cypher_query="""
    MATCH (ua:UserAccount)
    WHERE NOT (ua)<-[:HAS_ACCOUNT]-(:User)
    RETURN ua.id AS id, ua._ont_email AS email, ua._ont_source AS ontology_source
    """,
    cypher_visual_query="""
    MATCH (ua:UserAccount)
    WHERE NOT (ua)<-[:HAS_ACCOUNT]-(:User)
    RETURN ua
    """,
    cypher_count_query="""
    MATCH (ua:UserAccount)
    RETURN COUNT(ua) AS count
    """,
    asset_label="UserAccount",
    asset_id_field="id",
    identity_fields=("ontology_source", "id"),
    module=Module.CROSS_CLOUD,
    maturity=Maturity.STABLE,
)
```

`Module.CROSS_CLOUD` signals that the fact spans modules (via the ontology layer or otherwise).

## Available `_ont_*` properties

The exact set depends on the semantic label. See the schema docs at `docs/root/modules/ontology/schema.md` and the mapping source in `cartography/models/ontology/mapping/data/`. To make a new module participate, see the `enrich-ontology` skill.

## Tips

- Filter on `_ont_source` when a fact must only consider data from specific providers. When you
  return it, alias it `ontology_source` (or anything but `source`): `source` and `extra` are reserved
  `Finding` fields and `Fact.__post_init__` rejects a query that aliases them. Because an ontology
  node id is only unique per provider, include `ontology_source` in `identity_fields`.
- **Anchor on the label you match.** If `asset_label` is an ontology label, the `cypher_query` must
  match that label: `MATCH (k:APIKey) WHERE k:OpenAIApiKey OR k:OpenAIAdminApiKey ...`, never
  `MATCH (k) WHERE k:OpenAIApiKey ...`. Otherwise the rows returned and the asset claimed can
  diverge, and construction fails. Umbrella labels (`AWSPrincipal`, `EntraPrincipal`,
  `ScalewayPrincipal`, `APIKey`, ...) are preferable to a `labels(n) IN [...]` filter: they satisfy
  the anchor contract and use the label index.
- Cross-cloud detections become trivial: a single `MATCH (:Database)` covers `AWSRDSInstance`, `AWSDynamoDBTable`, `BigQueryDataset`, etc., once those modules opt into the `Database` label.
- Pair ontology facts with provider-specific facts in the same `Rule` to give operators both the unified view and the per-provider drill-down.
