## Spacelift Schema

```mermaid
graph LR

A(SpaceliftAccount) -- RESOURCE --> S(SpaceliftSpace)
A -- RESOURCE --> St(SpaceliftStack)
A -- RESOURCE --> U(SpaceliftUser)
A -- RESOURCE --> WP(SpaceliftWorkerPool)
A -- RESOURCE --> W(SpaceliftWorker)
A -- RESOURCE --> R(SpaceliftRun)
A -- RESOURCE --> C(SpaceliftGitCommit)

S -- CONTAINS --> S2(SpaceliftSpace)
St -- CONTAINS --> St2(SpaceliftStack)
WP -- CONTAINS --> W2(SpaceliftWorker)

St -- GENERATES --> R
U -- TRIGGERED --> R
W -- EXECUTES --> R
C -- COMMITTED --> R
R -- AFFECTS --> EC2(EC2Instance)

U -- HAS_ROLE_IN --> S
C -- CONFIRMED --> U

GH(GitHubUser) -- PUSHED --> C
```

### SpaceliftAccount

Representation of a single Spacelift Account (organization). This node represents the root organizational unit that contains all other Spacelift resources.

| Field | Description |
|-------|-------------|
| firstseen | Timestamp of when a sync job first created this node |
| lastupdated | Timestamp of the last time the node was updated |
| id | The unique account ID within Spacelift |
| spacelift_account_id | The Spacelift account identifier |
| name | Display name of the Spacelift account |

#### Relationships

- SpaceliftAccount contains all other Spacelift resources via RESOURCE relationships:

    ```
    (SpaceliftAccount)-[RESOURCE]->(SpaceliftSpace)
    (SpaceliftAccount)-[RESOURCE]->(SpaceliftStack)
    (SpaceliftAccount)-[RESOURCE]->(SpaceliftUser)
    (SpaceliftAccount)-[RESOURCE]->(SpaceliftWorkerPool)
    (SpaceliftAccount)-[RESOURCE]->(SpaceliftWorker)
    (SpaceliftAccount)-[RESOURCE]->(SpaceliftRun)
    (SpaceliftAccount)-[RESOURCE]->(SpaceliftGitCommit)
    ```

### SpaceliftSpace

Representation of an organizational container within Spacelift. Spaces can contain stacks, policies, contexts, modules, and worker pools. They form a hierarchy where root spaces belong directly to an account, and child spaces belong to parent spaces.

| Field | Description |
|-------|-------------|
| firstseen | Timestamp of when a sync job first created this node |
| lastupdated | Timestamp of the last time the node was updated |
| id | The unique space ID |
| name | Name of the space |
| description | Description of the space |
| is_root | Whether this is a root space (belongs directly to account) |
| spacelift_account_id | ID of the Spacelift account this space belongs to |
| parent_spacelift_account_id | ID of the parent Spacelift account (set only for root spaces) |
| parent_space_id | ID of the parent space (set only for child spaces) |

#### Relationships

- SpaceliftSpaces belong to a SpaceliftAccount:

    ```
    (SpaceliftSpace)<-[RESOURCE]-(SpaceliftAccount)
    ```

- SpaceliftSpaces can contain child spaces:

    ```
    (SpaceliftSpace)<-[CONTAINS]-(SpaceliftSpace)
    ```

- SpaceliftUsers can have roles in spaces:

    ```
    (SpaceliftUser)-[HAS_ROLE_IN{role}]->(SpaceliftSpace)
    ```

    The `role` property indicates the user's role (e.g., "admin", "read", "write").

### SpaceliftUser

Representation of a human or machine identity that interacts with Spacelift. Users can have roles in different spaces and can trigger runs, approve changes, and manage resources.

| Field | Description |
|-------|-------------|
| firstseen | Timestamp of when a sync job first created this node |
| lastupdated | Timestamp of the last time the node was updated |
| id | The unique user ID |
| username | Username of the user |
| email | Email address of the user |
| name | Full name of the user |
| user_type | Type of user (e.g., "human" or "machine") |

#### Relationships

- SpaceliftUsers belong to a SpaceliftAccount:

    ```
    (SpaceliftUser)<-[RESOURCE]-(SpaceliftAccount)
    ```

- SpaceliftUsers can have roles in spaces:

    ```
    (SpaceliftUser)-[HAS_ROLE_IN{role}]->(SpaceliftSpace)
    ```

    The `role` property indicates the user's role in that space.

- SpaceliftUsers can trigger runs:

    ```
    (SpaceliftUser)-[TRIGGERED]->(SpaceliftRun)
    ```

### SpaceliftStack

Representation of the fundamental building block of Spacelift infrastructure management. A stack combines source code (from VCS), current state (e.g., Terraform state), and configuration (environment variables, mounted files) into an isolated, independent entity.

| Field | Description |
|-------|-------------|
| firstseen | Timestamp of when a sync job first created this node |
| lastupdated | Timestamp of the last time the node was updated |
| id | The unique stack ID |
| name | Name of the stack |
| description | Description of the stack |
| state | Current state of the stack |
| administrative | Whether this is an administrative stack |
| repository | VCS repository URL for the stack |
| branch | Git branch the stack monitors |
| project_root | Directory in repo containing infrastructure code |
| space_id | ID of the space this stack belongs to |
| spacelift_account_id | ID of the Spacelift account this stack belongs to |

#### Relationships

- SpaceliftStacks belong to a SpaceliftAccount:

    ```
    (SpaceliftStack)<-[RESOURCE]-(SpaceliftAccount)
    ```

- SpaceliftStacks belong to a SpaceliftSpace:

    ```
    (SpaceliftStack)<-[CONTAINS]-(SpaceliftSpace)
    ```

- SpaceliftStacks generate runs:

    ```
    (SpaceliftStack)-[GENERATED]->(SpaceliftRun)
    ```

### SpaceliftWorkerPool

Representation of a collection of workers that execute Spacelift runs. Worker pools can be public (managed by Spacelift) or private (managed by the customer). They provide isolation, security, and control over where infrastructure operations execute.

| Field | Description |
|-------|-------------|
| firstseen | Timestamp of when a sync job first created this node |
| lastupdated | Timestamp of the last time the node was updated |
| id | The unique worker pool ID |
| name | Name of the worker pool |
| description | Description of the worker pool |
| pool_type | Type of worker pool (e.g., "public", "private") |
| space_id | ID of the space this worker pool belongs to |
| spacelift_account_id | ID of the Spacelift account this worker pool belongs to |

#### Relationships

- SpaceliftWorkerPools belong to a SpaceliftAccount:

    ```
    (SpaceliftWorkerPool)<-[RESOURCE]-(SpaceliftAccount)
    ```

- SpaceliftWorkerPools belong to a SpaceliftSpace:

    ```
    (SpaceliftWorkerPool)<-[CONTAINS]-(SpaceliftSpace)
    ```

- SpaceliftWorkerPools contain workers:

    ```
    (SpaceliftWorkerPool)-[CONTAINS]->(SpaceliftWorker)
    ```

### SpaceliftWorker

Representation of a logical execution unit that processes runs. Workers are compute resources that execute infrastructure operations inside Docker containers. Each worker processes one run at a time.

| Field | Description |
|-------|-------------|
| firstseen | Timestamp of when a sync job first created this node |
| lastupdated | Timestamp of the last time the node was updated |
| id | The unique worker ID |
| name | Name of the worker |
| status | Current status of the worker |
| worker_pool_id | ID of the worker pool this worker belongs to |
| spacelift_account_id | ID of the Spacelift account this worker belongs to |

#### Relationships

- SpaceliftWorkers belong to a SpaceliftAccount:

    ```
    (SpaceliftWorker)<-[RESOURCE]-(SpaceliftAccount)
    ```

- SpaceliftWorkers belong to a SpaceliftWorkerPool:

    ```
    (SpaceliftWorker)<-[CONTAINS]-(SpaceliftWorkerPool)
    ```

- SpaceliftWorkers execute runs:

    ```
    (SpaceliftWorker)-[EXECUTED]->(SpaceliftRun)
    ```

### SpaceliftRun

Representation of a job that can touch infrastructure. It is the execution instance of a stack's configuration. Runs track the entire lifecycle from creation through execution to completion, including state changes, outputs, and resource modifications.

| Field | Description |
|-------|-------------|
| firstseen | Timestamp of when a sync job first created this node |
| lastupdated | Timestamp of the last time the node was updated |
| id | The unique run ID |
| run_type | Type of run (e.g., "tracked", "proposed", "task") |
| state | Current state of the run |
| commit_sha | Git commit SHA that triggered this run |
| branch | Git branch this run belongs to |
| created_at | Timestamp when the run was created |
| stack_id | ID of the stack this run belongs to |
| triggered_by_user_id | ID of the user who triggered this run |
| spacelift_account_id | ID of the Spacelift account this run belongs to |

#### Relationships

- SpaceliftRuns belong to a SpaceliftAccount:

    ```
    (SpaceliftRun)<-[RESOURCE]-(SpaceliftAccount)
    ```

- SpaceliftRuns are generated by SpaceliftStacks:

    ```
    (SpaceliftRun)<-[GENERATED]-(SpaceliftStack)
    ```

- SpaceliftRuns are triggered by SpaceliftUsers:

    ```
    (SpaceliftRun)<-[TRIGGERED]-(SpaceliftUser)
    ```

- SpaceliftRuns are executed by SpaceliftWorkers:

    ```
    (SpaceliftRun)<-[EXECUTED]-(SpaceliftWorker)
    ```

- SpaceliftRuns are linked to the Git commit that triggered them:

    ```
    (SpaceliftRun)<-[COMMITTED]-(SpaceliftGitCommit)
    ```

- SpaceliftRuns can affect EC2 Instances:

    ```
    (SpaceliftRun)-[AFFECTED]->(EC2Instance)
    ```

    This relationship is created from **two sources**, and a single EC2 instance may have multiple `AFFECTED` relationships to different runs:

    **Source 1: Spacelift Entities API (always created during runs sync)**
    - Created automatically when Spacelift reports managed resources via its entities API
    - Properties: `lastupdated` only
    - Represents the current Terraform state view of managed instances
    - The Instance Id from spacelift is often seen in hex format (seen when using workerpools), causing a mistmatch with the InstanceID on an EC2 Node. (Hence the need for Source 2)

    **Source 2: CloudTrail Data (optional, requires EC2 ownership configuration)**
    - Created via MatchLink using CloudTrail data from S3
    - Additional properties with CloudTrail metadata:
      - `event_time`: Timestamp of the CloudTrail event
      - `event_name`: Name of the AWS API call (e.g., "RunInstances", "TerminateInstances")
      - `aws_account`: AWS account ID where the event occurred
      - `aws_region`: AWS region where the event occurred
    - Loaded separately by the `ec2_ownership` module
    - Requires CLI configuration: `--spacelift-ec2-ownership-s3-bucket`, `--spacelift-ec2-ownership-s3-key`, and optionally `--spacelift-ec2-ownership-aws-profile`

    Both relationships provide complementary views: the entities API shows current Terraform state, while CloudTrail shows historical AWS API interactions.

### SpaceliftGitCommit

Representation of a Git commit that triggered a Spacelift run. It contains metadata about the commit including the author, message, and timestamp.

| Field | Description |
|-------|-------------|
| firstseen | Timestamp of when a sync job first created this node |
| lastupdated | Timestamp of the last time the node was updated |
| id | The Git commit SHA (used as unique identifier) |
| sha | The Git commit SHA |
| message | Commit message |
| timestamp | ISO 8601 timestamp of when the commit was made |
| url | URL to view the commit in VCS |
| author_login | Login/username of the commit author |
| author_name | Full name of the commit author |

#### Relationships

- SpaceliftGitCommits belong to a SpaceliftAccount:

    ```
    (SpaceliftGitCommit)<-[RESOURCE]-(SpaceliftAccount)
    ```

- SpaceliftGitCommits are confirmed by SpaceliftUsers:

    ```
    (SpaceliftGitCommit)-[CONFIRMED]->(SpaceliftUser)
    ```

    This links commits to the human developers who wrote and confirmed the code, even when the deployment was triggered by an automated system (vcs/commit).

- SpaceliftGitCommits are linked to the runs that use them:

    ```
    (SpaceliftGitCommit)-[COMMITTED]->(SpaceliftRun)
    ```

- GitHubUsers can be linked to the commits they authored:

    ```
    (GitHubUser)-[PUSHED]->(SpaceliftGitCommit)
    ```

    This relationship links GitHub users to commits deployed via Spacelift by matching `GitHubUser.username` with `SpaceliftGitCommit.author_login`. It provides full traceability from infrastructure changes back to the developers who wrote the code.
