## CVE Schema

### CVE

Representation of a [CVE](https://github.com/CVEProject/automation-working-group/blob/master/cve_json_schema/DRAFT-JSON-file-format-v4.md)

| Field | Description |
|-------|--------------|
| firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| id | The CVE ID |
| assigner | The assigner of the CVE (email address) |
| description\_en | The english description of the issue. |
| references | This is reference data in the form of URLs |
| problem\_types | A list of CWE identifiers |
| vector\_string | The CVSSv3 scoring data. |
| attack\_vector | The attack vector |
| attack\_complexity | The attack complexity |
| privileges\_required | The privileges required |
| user\_interaction | The user interaction |
| scope | The scope |
| confidentiality\_impact | The confidentiality impact |
| integrity\_impact | The integrity impact |
| availability\_impact | The availability impact |
| base\_score | The CVSSv3 score |
| base\_severity | The severity |
| exploitability\_score | The exploitability score |
| impact\_score | The impact score |
| published\_date | The date the CVE was published |
| last\_modified\_date | The date the CVE was last updated |

#### Relationships

- A CVE linked to a SemgrepSCAFinding (optional)

    ```
    (CVE)-[:LINKED_TO]->(:SemgrepSCAFinding)
    ```
