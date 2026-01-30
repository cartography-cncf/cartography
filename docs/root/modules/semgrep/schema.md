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


#### Relationships

- An SemgrepSCAFinding connected to a GithubRepository (optional)

    ```
    (SemgrepSCAFinding)-[FOUND_IN]->(GithubRepository)
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

- A SemgrepDependency is required by a GithubRepository (optional)

    ```
    (:SemgrepDependency)<-[:REQUIRES{specifier, transitivity, url}]-(:GithubRepository)
    ```

    - specifier: A string describing the library version required by the repo (e.g. "==1.0.2")
    - transitivity: A string describing whether the dependency is direct or [transitive](https://en.wikipedia.org/wiki/Transitive_dependency) (e.g. direct, transitive)
    - url: The URL where the dependency is defined (e.g. `https://github.com/org/repo/blob/00000000000000000000000000000000/go.mod#L6`)
