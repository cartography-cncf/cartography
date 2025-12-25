## GitLab Schema

```mermaid
graph LR

O(GitLabOrganization) -- RESOURCE --> G(GitLabGroup)
O -- RESOURCE --> P(GitLabProject)
G -- MEMBER_OF --> G
P -- MEMBER_OF --> G
U(GitLabUser) -- MEMBER_OF --> O
U -- MEMBER_OF --> G
U -- MEMBER_OF --> P
U -- COMMITTED_TO --> P
P -- RESOURCE --> B(GitLabBranch)
P -- RESOURCE --> DF(GitLabDependencyFile)
P -- REQUIRES --> D(GitLabDependency)
DF -- HAS_DEP --> D
```

### GitLabOrganization

Representation of a GitLab top-level group (organization). In GitLab, organizations are typically the root-level groups that contain projects and nested subgroups.

| Field | Description |
|-------|--------------|
| firstseen | Timestamp of when a sync job first created this node |
| lastupdated | Timestamp of the last time the node was updated |
| **id** | The web URL of the GitLab organization/group |
| **name** | Name of the organization |
| **path** | URL path slug |
| **full_path** | Full path including all parent groups |
| description | Description of the organization |
| visibility | Visibility level (private, internal, public) |
| parent_id | Parent group ID (null for top-level organizations) |
| created_at | GitLab timestamp from when the organization was created |

#### Relationships

- GitLabOrganizations contain GitLabGroups (nested subgroups).

    ```
    (GitLabOrganization)-[RESOURCE]->(GitLabGroup)
    ```

- GitLabOrganizations contain GitLabProjects.

    ```
    (GitLabOrganization)-[RESOURCE]->(GitLabProject)
    ```

- GitLabUsers can be members of GitLabOrganizations with different access levels.

    ```
    (GitLabUser)-[MEMBER_OF{role, access_level}]->(GitLabOrganization)
    ```

    The `role` property can be: owner, maintainer, developer, reporter, guest.
    The `access_level` property corresponds to GitLab's numeric levels: 50, 40, 30, 20, 10.

### GitLabGroup

Representation of a GitLab nested subgroup. Groups can contain other groups (creating a hierarchy) and projects.

| Field | Description |
|-------|--------------|
| firstseen | Timestamp of when a sync job first created this node |
| lastupdated | Timestamp of the last time the node was updated |
| **id** | The web URL of the GitLab group |
| **name** | Name of the group |
| **path** | URL path slug |
| **full_path** | Full path including all parent groups |
| description | Description of the group |
| visibility | Visibility level (private, internal, public) |
| parent_id | Parent group ID |
| created_at | GitLab timestamp from when the group was created |

#### Relationships

- GitLabGroups are resources under GitLabOrganizations.

    ```
    (GitLabOrganization)-[RESOURCE]->(GitLabGroup)
    ```

- GitLabGroups can be members of parent GitLabGroups (nested structure).

    ```
    (GitLabGroup)-[MEMBER_OF]->(GitLabGroup)
    ```

- GitLabProjects can be members of GitLabGroups.

    ```
    (GitLabProject)-[MEMBER_OF]->(GitLabGroup)
    ```

- GitLabUsers can be members of GitLabGroups with different access levels.

    ```
    (GitLabUser)-[MEMBER_OF{role, access_level}]->(GitLabGroup)
    ```

### GitLabProject

Representation of a GitLab project (repository). Projects are GitLab's equivalent of repositories and can belong to organizations or groups.

| Field | Description |
|-------|--------------|
| firstseen | Timestamp of when a sync job first created this node |
| lastupdated | Timestamp of the last time the node was updated |
| **id** | The web URL of the GitLab project |
| **name** | Name of the project |
| **path** | URL path slug |
| **path_with_namespace** | Full path including namespace |
| description | Description of the project |
| visibility | Visibility level (private, internal, public) |
| default_branch | Default branch name (e.g., main, master) |
| archived | Whether the project is archived |
| created_at | GitLab timestamp from when the project was created |
| last_activity_at | GitLab timestamp of last activity |
| languages | JSON string containing detected programming languages and their percentages (e.g., `{"Python": 65.5, "JavaScript": 34.5}`) |

#### Sample Language Queries

Get all unique languages used across your GitLab estate:

```cypher
MATCH (p:GitLabProject)
WHERE p.languages IS NOT NULL
WITH p, apoc.convert.fromJsonMap(p.languages) AS langs
UNWIND keys(langs) AS language
RETURN DISTINCT language
ORDER BY language
```

Find all projects using a specific language (e.g., Python):

```cypher
MATCH (p:GitLabProject)
WHERE p.languages CONTAINS '"Python"'
RETURN p.name, p.languages
```

Get language distribution with project counts:

```cypher
MATCH (p:GitLabProject)
WHERE p.languages IS NOT NULL
WITH p, apoc.convert.fromJsonMap(p.languages) AS langs
UNWIND keys(langs) AS language
WITH language, langs[language] AS percentage, p
RETURN language, count(p) AS project_count, avg(percentage) AS avg_percentage
ORDER BY project_count DESC
```

**Note:** The `CONTAINS` query does a string search and works without APOC. For more precise queries (like filtering by percentage), use `apoc.convert.fromJsonMap()` to parse the JSON.

#### Relationships

- GitLabProjects belong to GitLabOrganizations.

    ```
    (GitLabOrganization)-[RESOURCE]->(GitLabProject)
    ```

- GitLabProjects can be members of GitLabGroups.

    ```
    (GitLabProject)-[MEMBER_OF]->(GitLabGroup)
    ```

- GitLabUsers can be members of GitLabProjects with different access levels.

    ```
    (GitLabUser)-[MEMBER_OF{role, access_level}]->(GitLabProject)
    ```

    The `role` property can be: owner, maintainer, developer, reporter, guest.
    The `access_level` property corresponds to GitLab's numeric levels: 50, 40, 30, 20, 10.

- GitLabUsers who have committed to GitLabProjects are tracked with commit activity data.

    ```
    (GitLabUser)-[COMMITTED_TO]->(GitLabProject)
    ```

    This relationship includes the following properties:
    - **commit_count**: Number of commits made by the user to the project
    - **last_commit_date**: Timestamp of the user's most recent commit to the project
    - **first_commit_date**: Timestamp of the user's oldest commit to the project

- GitLabProjects have GitLabBranches.

    ```
    (GitLabProject)-[RESOURCE]->(GitLabBranch)
    ```

- GitLabProjects have GitLabDependencyFiles.

    ```
    (GitLabProject)-[RESOURCE]->(GitLabDependencyFile)
    ```

- GitLabProjects require GitLabDependencies.

    ```
    (GitLabProject)-[REQUIRES]->(GitLabDependency)
    ```

### GitLabUser

Representation of a GitLab user. Users can be members of organizations, groups, and projects.

| Field | Description |
|-------|--------------|
| firstseen | Timestamp of when a sync job first created this node |
| lastupdated | Timestamp of the last time the node was updated |
| **id** | The web URL of the GitLab user |
| **username** | Username of the user |
| name | Full name of the user |
| state | State of the user (active, blocked, etc.) |
| email | Email address of the user (if public) |
| is_admin | Whether the user is an admin |

#### Relationships

- GitLabUsers can be members of GitLabOrganizations.

    ```
    (GitLabUser)-[MEMBER_OF{role, access_level}]->(GitLabOrganization)
    ```

- GitLabUsers can be members of GitLabGroups.

    ```
    (GitLabUser)-[MEMBER_OF{role, access_level}]->(GitLabGroup)
    ```

- GitLabUsers can be members of GitLabProjects.

    ```
    (GitLabUser)-[MEMBER_OF{role, access_level}]->(GitLabProject)
    ```

- GitLabUsers who have committed to GitLabProjects are tracked.

    ```
    (GitLabUser)-[COMMITTED_TO{commit_count, last_commit_date, first_commit_date}]->(GitLabProject)
    ```

### GitLabBranch

Representation of a GitLab branch within a project.

| Field | Description |
|-------|--------------|
| firstseen | Timestamp of when a sync job first created this node |
| lastupdated | Timestamp of the last time the node was updated |
| **id** | Unique identifier: `{project_url}/tree/{branch_name}` |
| **name** | Name of the branch |
| protected | Whether the branch is protected |
| default | Whether this is the default branch |
| web_url | Web URL to view the branch |

#### Relationships

- GitLabProjects have GitLabBranches.

    ```
    (GitLabProject)-[RESOURCE]->(GitLabBranch)
    ```

### GitLabDependencyFile

Representation of a dependency manifest file (e.g., package.json, requirements.txt, pom.xml) within a GitLab project.

| Field | Description |
|-------|--------------|
| firstseen | Timestamp of when a sync job first created this node |
| lastupdated | Timestamp of the last time the node was updated |
| **id** | Unique identifier: `{project_url}/blob/{file_path}` |
| **path** | Path to the file in the repository |
| **filename** | Name of the file (e.g., package.json) |

#### Relationships

- GitLabProjects have GitLabDependencyFiles.

    ```
    (GitLabProject)-[RESOURCE]->(GitLabDependencyFile)
    ```

- GitLabDependencyFiles contain GitLabDependencies.

    ```
    (GitLabDependencyFile)-[HAS_DEP]->(GitLabDependency)
    ```

### GitLabDependency

Representation of a software dependency from GitLab's dependency scanning artifacts (Gemnasium). This node contains information about a package dependency detected via GitLab's security scanning.

| Field | Description |
|-------|--------------|
| firstseen | Timestamp of when a sync job first created this node |
| lastupdated | Timestamp of the last time the node was updated |
| **id** | Unique identifier: `{project_url}:{package_manager}:{name}@{version}` |
| **name** | Name of the dependency |
| **version** | Version of the dependency |
| **package_manager** | Package manager (npm, pip, maven, etc.) |

#### Relationships

- GitLabProjects require GitLabDependencies.

    ```
    (GitLabProject)-[REQUIRES]->(GitLabDependency)
    ```

- GitLabDependencyFiles contain GitLabDependencies (when the manifest file can be determined).

    ```
    (GitLabDependencyFile)-[HAS_DEP]->(GitLabDependency)
    ```
