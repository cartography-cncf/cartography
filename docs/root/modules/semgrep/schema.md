## Semgrep Schema

### SemgrepDeployment

Represents a Semgrep [Deployment](https://semgrep.dev/api/v1/docs/#tag/Deployment), a unit encapsulating a security organization inside Semgrep Cloud. Works as the parent of all other Semgrep resources.

| Field | Description |
|-------|--------------|
| firstseen | Timestamp of when a sync job first discovered this node  |
| lastupdated | Timestamp of the last time the node was updated |
| **id** | Unique integer id representing the deployment |
| **slug** | Lowercase string id representing the deployment to query the API |
| **name** | Name of security organization connected to the deployment |

#### Relationships

- A SemgrepDeployment contains SemgrepSASTFinding's

    ```
    (SemgrepDeployment)-[RESOURCE]->(SemgrepSASTFinding)
    ```

- A SemgrepDeployment contains SemgrepSCAFinding's

    ```
    (SemgrepDeployment)-[RESOURCE]->(SemgrepSCAFinding)
    ```

- A SemgrepDeployment contains SemgrepSCALocation's

    ```
    (SemgrepDeployment)-[RESOURCE]->(SemgrepSCALocation)
    ```

- A SemgrepDeployment contains SemgrepDependency's

    ```
    (SemgrepDeployment)-[RESOURCE]->(SemgrepDependency)
    ```

- A SemgrepDeployment contains SemgrepFindingAssistant's

    ```
    (SemgrepDeployment)-[RESOURCE]->(SemgrepFindingAssistant)
    ```

- A SemgrepDeployment contains SemgrepSecretsFinding's

    ```
    (SemgrepDeployment)-[RESOURCE]->(SemgrepSecretsFinding)
    ```

### SemgrepSASTFinding::SecurityIssue

Represents a [Semgrep SAST](https://semgrep.dev/docs/semgrep-code/getting-started/) finding. This is a code-level security issue discovered by Semgrep static analysis (SAST). Before ingesting this node, make sure you have run Semgrep CI and that it's connected to Semgrep Cloud Platform [Running Semgrep CI with Semgrep Cloud Platform](https://semgrep.dev/docs/semgrep-ci/running-semgrep-ci-with-semgrep-cloud-platform/). The API called to retrieve this information is documented at https://semgrep.dev/api/v1/docs/#tag/FindingsService/operation/FindingsService_ListFindings.

> **Ontology Mapping**: This node has the extra label `SecurityIssue` to enable cross-scanner queries for non-CVE security issues across different tools (e.g., GuardDutyFinding, SemgrepSecretsFinding, AzureSecurityAssessment).

| Field | Description |
|-------|--------------|
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |
| **id** | Unique integer id of the finding taken from Semgrep API |
| **rule_id** | The rule that triggered the finding |
| **repository** | The repository path where the finding was discovered |
| **branch** | The branch where the finding was discovered |
| title | Short title for the finding, set to the rule id |
| description | Description of the vulnerability from the rule message |
| severity | Severity of the finding (e.g. CRITICAL, HIGH, MEDIUM, LOW) |
| confidence | Confidence of the finding (e.g. HIGH, MEDIUM, LOW) |
| categories | List of finding categories (e.g. security) |
| cwe_names | List of CWE identifiers associated with the rule |
| owasp_names | List of OWASP category names associated with the rule |
| file_path | Path of the file where the finding was discovered |
| start_line | Line where the finding starts |
| start_col | Column where the finding starts |
| end_line | Line where the finding ends |
| end_col | Column where the finding ends |
| line_of_code_url | URL pointing to the exact line of code in the repository |
| state | Current state of the finding (e.g. unresolved, fixed, removed, muted) |
| fix_status | Fix status based on triage (e.g. open, fixed, ignored) |
| triage_status | Triage status of the finding (e.g. untriaged, ignored, reopened) |
| opened_at | Date and time when the finding was first seen in UTC |
| repository_url | Full URL of the repository where the finding was discovered (e.g. `https://github.com/org/repo`) |
| risk_severity | Risk level computed by post-ingestion analysis. INFO for archived repos, otherwise equals severity. See [semgrep_sast_risk_analysis.json](https://github.com/cartography-cncf/cartography/blob/master/cartography/data/jobs/scoped_analysis/semgrep_sast_risk_analysis.json) for further details |

#### Relationships

- A SemgrepSASTFinding connected to a GitHubRepository (optional)

    ```
    (SemgrepSASTFinding)-[FOUND_IN]->(GitHubRepository)
    ```

- A SemgrepSASTFinding has a SemgrepFindingAssistant (optional)

    ```
    (SemgrepSASTFinding)-[HAS_ASSISTANT]->(SemgrepFindingAssistant)
    ```

### SemgrepSecretsFinding::SecurityIssue

Represents a [Semgrep Secrets](https://semgrep.dev/docs/semgrep-secrets/conceptual-overview/) finding. This is a hardcoded secret (e.g. API key, token, credential) discovered by Semgrep scanning source code. Before ingesting this node, make sure you have run Semgrep CI and that it's connected to Semgrep Cloud Platform [Running Semgrep CI with Semgrep Cloud Platform](https://semgrep.dev/docs/semgrep-ci/running-semgrep-ci-with-semgrep-cloud-platform/). The API called to retrieve this information is documented at https://semgrep.dev/api/v1/docs/#tag/SecretsService.

> **Ontology Mapping**: This node has the extra label `SecurityIssue` to enable cross-scanner queries for non-CVE security issues across different tools (e.g., GuardDutyFinding, SemgrepSASTFinding, AzureSecurityAssessment).

| Field | Description |
|-------|--------------|
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |
| **id** | Unique integer id of the finding taken from Semgrep API |
| **rule_hash_id** | Hash id of the rule that triggered the finding |
| **repository_name** | The repository path where the finding was discovered (e.g. `org/repo`) |
| **ref** | The branch or ref where the finding was discovered |
| severity | Severity of the finding (e.g. HIGH, MEDIUM, LOW) |
| confidence | Confidence level of the finding (e.g. HIGH, MEDIUM, LOW) |
| type | Type of secret detected (e.g. `OpenAI`, `GitHub`, `AWS`) |
| validation_state | Whether the secret has been validated (e.g. `CONFIRMED_VALID`, `CONFIRMED_INVALID`, `VALIDATION_ERROR`, `NO_VALIDATOR`) |
| status | Current status of the finding (e.g. `OPEN`, `FIXED`, `IGNORED`) |
| finding_path | Path and line number where the secret was found (e.g. `src/config.py:42`) |
| finding_path_url | URL pointing to the exact location of the secret in the repository |
| ref_url | URL of the branch/ref where the finding was discovered |
| mode | Semgrep mode under which the finding was detected (e.g. `MONITOR`, `BLOCK`) |
| created_at | Date and time when the finding was first seen in UTC |
| updated_at | Date and time when the finding was last updated in UTC |
| repository_visibility | Visibility of the repository (e.g. `PUBLIC`, `PRIVATE`) |
| repository_scm_type | Source control management system of the repository (e.g. `GITHUB`) |
| repository_url | Full URL of the repository where the finding was discovered (e.g. `https://github.com/org/repo`) |

#### Relationships

- A SemgrepSecretsFinding belongs to a SemgrepDeployment

    ```
    (SemgrepDeployment)-[RESOURCE]->(SemgrepSecretsFinding)
    ```

- A SemgrepSecretsFinding connected to a GitHubRepository (optional)

    ```
    (SemgrepSecretsFinding)-[FOUND_IN]->(GitHubRepository)
    ```

### SemgrepSCAFinding

Represents a [Semgrep Supply Chain](https://semgrep.dev/docs/semgrep-supply-chain/overview/) finding. This is, a vulnerability in a dependency of a project discovered by Semgrep performing software composition analysis (SCA) and code reachability analysis. Before ingesting this node, make sure you have run Semgrep CI and that it's connected to Semgrep Cloud Platform [Running Semgrep CI with Semgrep Cloud Platform](https://semgrep.dev/docs/semgrep-ci/running-semgrep-ci-with-semgrep-cloud-platform/). The API called to retrieve this information is documented at https://semgrep.dev/api/v1/docs/#tag/SupplyChainService.

| Field | Description |
|-------|--------------|
| firstseen | Timestamp of when a sync job first discovered this node  |
| lastupdated | Timestamp of the last time the node was updated |
| **id** | Unique id of the finding taken from Semgrep API |
| **rule_id** | The rule that triggered the finding |
| **repository** | The repository path where the finding was discovered |
| **branch** | The branch where the finding was discovered |
| summary | A short title summarizing of the finding |
| description | Description of the vulnerability. |
| package_manager | The ecosystem of the dependency where the finding was discovered (e.g. pypi, npm, maven) |
| severity | Severity of the finding based on Semgrep analysis (e.g. CRITICAL, HIGH, MEDIUM, LOW) |
| cve_id | CVE id of the vulnerability from NVD. Check [cve_schema](../cve/schema.md) |
| reachability_check | Whether the vulnerability reachability is confirmed, not confirmed or needs to be manually confirmed |
| reachability_condition | Description of the reachability condition (e.g. reachable if code is used in X way) |
| reachability | Whether the vulnerability is reachable or not |
| reachability_risk | Risk of the vulnerability (e.g. CRITICAL, HIGH, MEDIUM, LOW) based on severity and likelihod, the latter given by reachability status and reachability check. Risk calculation was based on [NIST 800-30r1](https://nvlpubs.nist.gov/nistpubs/legacy/sp/nistspecialpublication800-30r1.pdf) Appendix I - Riks Determination and the [reachability exposure](https://semgrep.dev/docs/semgrep-supply-chain/triage-and-remediation/#exposure-filters). See [semgrep_sca_risk_analysis.json](https://github.com/cartography-cncf/cartography/blob/master/cartography/data/jobs/scoped_analysis/semgrep_sca_risk_analysis.json) for further details |
| transitivity | Whether the vulnerability is transitive or not (e.g. dependency, transitive) |
| dependency | Dependency where the finding was discovered. Includes dependency name and version |
| dependency_fix | Dependency version that fixes the vulnerability |
| ref_urls | List of reference urls for the finding |
| dependency_file | Path of the file where the finding was discovered (e.g. lock.json, requirements.txt) |
| dependency_file_url | URL of the file where the finding was discovered |
| scan_time | Date and time when the finding was discovered in UTC |
| fix_status | Whether the finding is fixed or not based on triage (e.g. open, fixed, ignored) |
| triage_status | Whether the finding is triaged or not (e.g. untriaged, ignored, reopened) |
| confidence | Confidence of the finding based on Semgrep analysis (e.g. high, medium, low) |
| repository_url | Full URL of the repository where the finding was discovered (e.g. `https://github.com/org/repo`) |


#### Relationships

- An SemgrepSCAFinding connected to a GitHubRepository (optional)

    ```
    (SemgrepSCAFinding)-[FOUND_IN]->(GitHubRepository)
    ```

- A SemgrepSCAFinding vulnerable dependency usage at SemgrepSCALocation (optional)

    ```
    (SemgrepSCAFinding)-[USAGE_AT]->(SemgrepSCALocation)
    ```

- A SemgrepSCAFinding affects a Dependency (optional)

    ```
    (:SemgrepSCAFinding)-[:AFFECTS]->(:Dependency)
    ```

- A SemgrepSCAFinding linked to a CVE (optional)

    ```
    (:SemgrepSCAFinding)<-[:LINKED_TO]-(:CVE)
    ```

- A SemgrepSCAFinding has a SemgrepFindingAssistant (optional)

    ```
    (SemgrepSCAFinding)-[HAS_ASSISTANT]->(SemgrepFindingAssistant)
    ```

### SemgrepFindingAssistant

Represents [Semgrep Assistant](https://semgrep.dev/docs/semgrep-assistant/overview/) AI-generated data attached to a finding. Semgrep Assistant provides automated triage, remediation guidance, code fixes, and component analysis. The assistant node shares the same deployment sub-resource as its parent finding and is linked via `HAS_ASSISTANT`. Only present when Semgrep Assistant is enabled for the deployment.

| Field | Description |
|-------|--------------|
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |
| **id** | Unique id formed by the prefix `semgrep-assistant-` and the parent finding's integer id |
| autofix_fix_code | AI-generated source code fix for the finding. Review carefully before applying |
| autotriage_verdict | AI triage recommendation: `true_positive` to fix, `false_positive` to ignore |
| autotriage_reason | Reasoning for a `false_positive` verdict; empty string for `true_positive` |
| component_tag | AI-guessed tag describing the matched code's purpose (e.g. `user data`) |
| component_risk | Risk level of the component: `high`, `low`, or `neutral` |
| guidance_summary | Short title explaining how to fix the finding |
| guidance_instructions | Step-by-step remediation instructions for a developer |
| rule_explanation_summary | Concise summary of why the rule flagged this code |
| rule_explanation | Detailed explanation of why the rule flagged the code and what the security impact is |

#### Relationships

- A SemgrepFindingAssistant belongs to a SemgrepDeployment

    ```
    (SemgrepDeployment)-[RESOURCE]->(SemgrepFindingAssistant)
    ```

### SemgrepSCALocation

Represents the location in a repository where a vulnerable dependency is used in a way that can trigger the vulnerability.

| Field | Description |
|-------|--------------|
| firstseen | Timestamp of when a sync job first discovered this node  |
| lastupdated | Timestamp of the last time the node was updated |
| **id** | Unique id identifying the location of the finding |
| path | Path of the file where the usage was discovered |
| start_line | Line where the usage starts |
| start_col | Column where the usage starts |
| end_line | Line where the usage ends |
| end_col | Column where the usage ends |
| url | URL of the file where the usage was discovered |


### SemgrepDependency

Represents a dependency of a repository as returned by the Semgrep
[List dependencies API](https://semgrep.dev/api/v1/docs/#tag/SupplyChainService/operation/semgrep_app.products.sca.handlers.dependency.list_dependencies_conexxion).

| Field | Description |
|-------|--------------|
| firstseen | Timestamp of when a sync job first discovered this node  |
| lastupdated | Timestamp of the last time the node was updated |
| **id** | Unique id formed by the name and version of the dependency |
| name | Name of the dependency |
| version | Version of the dependency |
| ecosystem | Ecosystem of the dependency, e.g. "gomod" for dependencies defined in go.mod files. (see [API docs](https://semgrep.dev/api/v1/docs/#tag/SupplyChainService/operation/semgrep_app.products.sca.handlers.dependency.list_dependencies_conexxion) for full list of options) |


### GoLibrary

Represents a Go library dependency as listed in a go.mod file.
All GoLibrary nodes are also SemgrepDependency nodes.
See [SemgrepDependency](#semgrepdependency) for details.

### NpmLibrary

Represents a NPM library dependency as listed in a package-lock.json file.
All NpmLibrary nodes are also SemgrepDependency nodes.
See [SemgrepDependency](#semgrepdependency) for details.


#### Relationships

- A SemgrepDependency is required by a GitHubRepository (optional)

    ```
    (:SemgrepDependency)<-[:REQUIRES{specifier, transitivity, url}]-(:GitHubRepository)
    ```

    - specifier: A string describing the library version required by the repo (e.g. "==1.0.2")
    - transitivity: A string describing whether the dependency is direct or [transitive](https://en.wikipedia.org/wiki/Transitive_dependency) (e.g. direct, transitive)
    - url: The URL where the dependency is defined (e.g. `https://github.com/org/repo/blob/00000000000000000000000000000000/go.mod#L6`)
