"""
CIS Kubernetes RBAC Security Checks

Implements CIS Kubernetes Benchmark Section 5.1: RBAC and Service Accounts
Based on CIS Kubernetes Benchmark v1.12.0

Each Rule represents a distinct security concept with a consistent main node type.
Facts within a Rule are provider-specific implementations of the same concept.
"""

from cartography.rules.spec.model import Fact
from cartography.rules.spec.model import Finding
from cartography.rules.spec.model import Framework
from cartography.rules.spec.model import Maturity
from cartography.rules.spec.model import Module
from cartography.rules.spec.model import Rule
from cartography.rules.spec.model import RuleReference

CIS_REFERENCES = [
    RuleReference(
        text="CIS Kubernetes Benchmark v1.12.0",
        url="https://www.cisecurity.org/benchmark/kubernetes",
    ),
    RuleReference(
        text="Kubernetes RBAC Good Practices",
        url="https://kubernetes.io/docs/concepts/security/rbac-good-practices/",
    ),
]


# =============================================================================
# CIS K8s 5.1.1: cluster-admin role only used where required
# Main node: KubernetesClusterRoleBinding
# =============================================================================
class ClusterAdminUsageOutput(Finding):
    """Output model for cluster-admin role usage check."""

    binding_name: str | None = None
    subject_type: str | None = None
    subject_name: str | None = None
    cluster_name: str | None = None


_k8s_cluster_admin_usage = Fact(
    id="k8s_cluster_admin_usage",
    name="Kubernetes cluster-admin role bindings",
    description=(
        "Detects ClusterRoleBindings that grant the cluster-admin role. "
        "The cluster-admin role provides unrestricted access to all resources "
        "in the cluster and should only be used where absolutely necessary."
    ),
    cypher_query="""
    MATCH (cluster:KubernetesCluster)-[:RESOURCE]->(crb:KubernetesClusterRoleBinding)
    WHERE crb.role_name = 'cluster-admin'
    OPTIONAL MATCH (crb)-[:SUBJECT]->(sa:KubernetesServiceAccount)
    WITH cluster, crb, collect(sa) AS sas
    OPTIONAL MATCH (crb)-[:SUBJECT]->(u:KubernetesUser)
    WITH cluster, crb, sas, collect(u) AS users
    OPTIONAL MATCH (crb)-[:SUBJECT]->(g:KubernetesGroup)
    WITH cluster, crb, sas, users, collect(g) AS groups
    UNWIND (
        [sa IN sas | {subject_type: 'ServiceAccount', subject_name: sa.name}] +
        [u IN users | {subject_type: 'User', subject_name: u.name}] +
        [g IN groups | {subject_type: 'Group', subject_name: g.name}]
    ) AS subject
    RETURN
        crb.name AS binding_name,
        subject.subject_type AS subject_type,
        subject.subject_name AS subject_name,
        cluster.name AS cluster_name
    """,
    cypher_visual_query="""
    MATCH p=(cluster:KubernetesCluster)-[:RESOURCE]->(crb:KubernetesClusterRoleBinding)
          -[:ROLE_REF]->(cr:KubernetesClusterRole)
    WHERE crb.role_name = 'cluster-admin'
    RETURN *
    """,
    cypher_count_query="""
    MATCH (crb:KubernetesClusterRoleBinding)
    RETURN COUNT(crb) AS count
    """,
    asset_id_field="binding_name",
    module=Module.KUBERNETES,
    maturity=Maturity.EXPERIMENTAL,
)

cis_k8s_5_1_1_cluster_admin_usage = Rule(
    id="cis_k8s_5_1_1_cluster_admin_usage",
    name="CIS K8s 5.1.1: Cluster-Admin Role Usage",
    description=(
        "The cluster-admin role provides wide-ranging powers over the environment "
        "and should be used only where and when needed. Review all bindings to "
        "ensure cluster-admin privilege is required."
    ),
    output_model=ClusterAdminUsageOutput,
    facts=(_k8s_cluster_admin_usage,),
    tags=("rbac", "cluster-admin", "stride:elevation_of_privilege"),
    version="1.0.0",
    references=CIS_REFERENCES,
    frameworks=(
        Framework(
            name="CIS Kubernetes Benchmark",
            short_name="CIS",
            scope="kubernetes",
            revision="1.12",
            requirement="5.1.1",
        ),
    ),
)


# =============================================================================
# CIS K8s 5.1.2: Minimize access to secrets
# Main node: KubernetesClusterRole / KubernetesRole
# =============================================================================
class SecretAccessOutput(Finding):
    """Output model for secret access check."""

    role_name: str | None = None
    role_type: str | None = None
    verbs: str | None = None
    cluster_name: str | None = None


_k8s_secret_access_clusterroles = Fact(
    id="k8s_secret_access_clusterroles",
    name="Kubernetes ClusterRoles granting access to secrets",
    description=(
        "Detects ClusterRoles that grant get, list, or watch access to secrets. "
        "Access to secrets should be restricted to the smallest possible group "
        "of users to reduce the risk of privilege escalation."
    ),
    cypher_query="""
    MATCH (cluster:KubernetesCluster)-[:RESOURCE]->(cr:KubernetesClusterRole)
    WHERE 'secrets' IN cr.resources
      AND any(v IN cr.verbs WHERE v IN ['get', 'list', 'watch', '*'])
      AND NOT cr.name STARTS WITH 'system:'
    RETURN
        cr.name AS role_name,
        'ClusterRole' AS role_type,
        cr.verbs AS verbs,
        cluster.name AS cluster_name
    """,
    cypher_visual_query="""
    MATCH p=(cluster:KubernetesCluster)-[:RESOURCE]->(cr:KubernetesClusterRole)
    WHERE 'secrets' IN cr.resources
      AND any(v IN cr.verbs WHERE v IN ['get', 'list', 'watch', '*'])
      AND NOT cr.name STARTS WITH 'system:'
    RETURN *
    """,
    cypher_count_query="""
    MATCH (cr:KubernetesClusterRole)
    WHERE NOT cr.name STARTS WITH 'system:'
    RETURN COUNT(cr) AS count
    """,
    module=Module.KUBERNETES,
    maturity=Maturity.EXPERIMENTAL,
)

_k8s_secret_access_roles = Fact(
    id="k8s_secret_access_roles",
    name="Kubernetes Roles granting access to secrets",
    description=(
        "Detects namespace-scoped Roles that grant get, list, or watch access to secrets. "
        "Access to secrets should be restricted to the smallest possible group "
        "of users to reduce the risk of privilege escalation."
    ),
    cypher_query="""
    MATCH (cluster:KubernetesCluster)-[:RESOURCE]->(r:KubernetesRole)
    WHERE 'secrets' IN r.resources
      AND any(v IN r.verbs WHERE v IN ['get', 'list', 'watch', '*'])
      AND NOT r.name STARTS WITH 'system:'
    RETURN
        r.name AS role_name,
        'Role' AS role_type,
        r.verbs AS verbs,
        cluster.name AS cluster_name
    """,
    cypher_visual_query="""
    MATCH p=(cluster:KubernetesCluster)-[:RESOURCE]->(r:KubernetesRole)
    WHERE 'secrets' IN r.resources
      AND any(v IN r.verbs WHERE v IN ['get', 'list', 'watch', '*'])
      AND NOT r.name STARTS WITH 'system:'
    RETURN *
    """,
    cypher_count_query="""
    MATCH (r:KubernetesRole)
    WHERE NOT r.name STARTS WITH 'system:'
    RETURN COUNT(r) AS count
    """,
    module=Module.KUBERNETES,
    maturity=Maturity.EXPERIMENTAL,
)

cis_k8s_5_1_2_secret_access = Rule(
    id="cis_k8s_5_1_2_secret_access",
    name="CIS K8s 5.1.2: Roles Granting Access to Secrets",
    description=(
        "Access to secrets stored within the Kubernetes cluster should be restricted "
        "to the smallest possible group of users to reduce the risk of privilege escalation."
    ),
    output_model=SecretAccessOutput,
    facts=(_k8s_secret_access_clusterroles, _k8s_secret_access_roles),
    tags=("rbac", "secrets", "stride:information_disclosure"),
    version="1.0.0",
    references=CIS_REFERENCES,
    frameworks=(
        Framework(
            name="CIS Kubernetes Benchmark",
            short_name="CIS",
            scope="kubernetes",
            revision="1.12",
            requirement="5.1.2",
        ),
    ),
)


# =============================================================================
# CIS K8s 5.1.3: Minimize wildcard use in Roles and ClusterRoles
# Main node: KubernetesClusterRole / KubernetesRole
# =============================================================================
class WildcardRoleOutput(Finding):
    """Output model for wildcard role check."""

    role_name: str | None = None
    role_type: str | None = None
    wildcard_in: str | None = None
    cluster_name: str | None = None


_k8s_wildcard_clusterroles = Fact(
    id="k8s_wildcard_clusterroles",
    name="Kubernetes ClusterRoles with wildcard permissions",
    description=(
        "Detects ClusterRoles that use wildcard (*) in resources or verbs. "
        "Wildcard permissions grant broad access that may include future resources "
        "added to the API, violating the principle of least privilege."
    ),
    cypher_query="""
    MATCH (cluster:KubernetesCluster)-[:RESOURCE]->(cr:KubernetesClusterRole)
    WHERE ('*' IN cr.resources OR '*' IN cr.verbs)
      AND NOT cr.name STARTS WITH 'system:'
    RETURN
        cr.name AS role_name,
        'ClusterRole' AS role_type,
        CASE
            WHEN '*' IN cr.resources AND '*' IN cr.verbs THEN 'resources and verbs'
            WHEN '*' IN cr.resources THEN 'resources'
            ELSE 'verbs'
        END AS wildcard_in,
        cluster.name AS cluster_name
    """,
    cypher_visual_query="""
    MATCH p=(cluster:KubernetesCluster)-[:RESOURCE]->(cr:KubernetesClusterRole)
    WHERE ('*' IN cr.resources OR '*' IN cr.verbs)
      AND NOT cr.name STARTS WITH 'system:'
    RETURN *
    """,
    cypher_count_query="""
    MATCH (cr:KubernetesClusterRole)
    WHERE NOT cr.name STARTS WITH 'system:'
    RETURN COUNT(cr) AS count
    """,
    module=Module.KUBERNETES,
    maturity=Maturity.EXPERIMENTAL,
)

_k8s_wildcard_roles = Fact(
    id="k8s_wildcard_roles",
    name="Kubernetes Roles with wildcard permissions",
    description=(
        "Detects namespace-scoped Roles that use wildcard (*) in resources or verbs. "
        "Wildcard permissions grant broad access that may include future resources "
        "added to the API, violating the principle of least privilege."
    ),
    cypher_query="""
    MATCH (cluster:KubernetesCluster)-[:RESOURCE]->(r:KubernetesRole)
    WHERE ('*' IN r.resources OR '*' IN r.verbs)
      AND NOT r.name STARTS WITH 'system:'
    RETURN
        r.name AS role_name,
        'Role' AS role_type,
        CASE
            WHEN '*' IN r.resources AND '*' IN r.verbs THEN 'resources and verbs'
            WHEN '*' IN r.resources THEN 'resources'
            ELSE 'verbs'
        END AS wildcard_in,
        cluster.name AS cluster_name
    """,
    cypher_visual_query="""
    MATCH p=(cluster:KubernetesCluster)-[:RESOURCE]->(r:KubernetesRole)
    WHERE ('*' IN r.resources OR '*' IN r.verbs)
      AND NOT r.name STARTS WITH 'system:'
    RETURN *
    """,
    cypher_count_query="""
    MATCH (r:KubernetesRole)
    WHERE NOT r.name STARTS WITH 'system:'
    RETURN COUNT(r) AS count
    """,
    module=Module.KUBERNETES,
    maturity=Maturity.EXPERIMENTAL,
)

cis_k8s_5_1_3_wildcard_roles = Rule(
    id="cis_k8s_5_1_3_wildcard_roles",
    name="CIS K8s 5.1.3: Wildcard Use in Roles and ClusterRoles",
    description=(
        "Kubernetes Roles and ClusterRoles should not use wildcard (*) for resources "
        "or verbs. Wildcards grant broad access that may inadvertently include new "
        "resources added to the API."
    ),
    output_model=WildcardRoleOutput,
    facts=(_k8s_wildcard_clusterroles, _k8s_wildcard_roles),
    tags=("rbac", "wildcard", "least-privilege", "stride:elevation_of_privilege"),
    version="1.0.0",
    references=CIS_REFERENCES,
    frameworks=(
        Framework(
            name="CIS Kubernetes Benchmark",
            short_name="CIS",
            scope="kubernetes",
            revision="1.12",
            requirement="5.1.3",
        ),
    ),
)


# =============================================================================
# CIS K8s 5.1.4: Minimize access to create pods
# Main node: KubernetesClusterRole / KubernetesRole
# =============================================================================
class PodCreateAccessOutput(Finding):
    """Output model for pod creation access check."""

    role_name: str | None = None
    role_type: str | None = None
    cluster_name: str | None = None


_k8s_pod_create_clusterroles = Fact(
    id="k8s_pod_create_clusterroles",
    name="Kubernetes ClusterRoles granting pod creation",
    description=(
        "Detects ClusterRoles that grant create access to pods. "
        "The ability to create pods can provide privilege escalation "
        "opportunities such as assigning privileged service accounts."
    ),
    cypher_query="""
    MATCH (cluster:KubernetesCluster)-[:RESOURCE]->(cr:KubernetesClusterRole)
    WHERE ('pods' IN cr.resources OR '*' IN cr.resources)
      AND any(v IN cr.verbs WHERE v IN ['create', '*'])
      AND NOT cr.name STARTS WITH 'system:'
    RETURN
        cr.name AS role_name,
        'ClusterRole' AS role_type,
        cluster.name AS cluster_name
    """,
    cypher_visual_query="""
    MATCH p=(cluster:KubernetesCluster)-[:RESOURCE]->(cr:KubernetesClusterRole)
    WHERE ('pods' IN cr.resources OR '*' IN cr.resources)
      AND any(v IN cr.verbs WHERE v IN ['create', '*'])
      AND NOT cr.name STARTS WITH 'system:'
    RETURN *
    """,
    cypher_count_query="""
    MATCH (cr:KubernetesClusterRole)
    WHERE NOT cr.name STARTS WITH 'system:'
    RETURN COUNT(cr) AS count
    """,
    module=Module.KUBERNETES,
    maturity=Maturity.EXPERIMENTAL,
)

_k8s_pod_create_roles = Fact(
    id="k8s_pod_create_roles",
    name="Kubernetes Roles granting pod creation",
    description=(
        "Detects namespace-scoped Roles that grant create access to pods. "
        "The ability to create pods can provide privilege escalation "
        "opportunities such as assigning privileged service accounts."
    ),
    cypher_query="""
    MATCH (cluster:KubernetesCluster)-[:RESOURCE]->(r:KubernetesRole)
    WHERE ('pods' IN r.resources OR '*' IN r.resources)
      AND any(v IN r.verbs WHERE v IN ['create', '*'])
      AND NOT r.name STARTS WITH 'system:'
    RETURN
        r.name AS role_name,
        'Role' AS role_type,
        cluster.name AS cluster_name
    """,
    cypher_visual_query="""
    MATCH p=(cluster:KubernetesCluster)-[:RESOURCE]->(r:KubernetesRole)
    WHERE ('pods' IN r.resources OR '*' IN r.resources)
      AND any(v IN r.verbs WHERE v IN ['create', '*'])
      AND NOT r.name STARTS WITH 'system:'
    RETURN *
    """,
    cypher_count_query="""
    MATCH (r:KubernetesRole)
    WHERE NOT r.name STARTS WITH 'system:'
    RETURN COUNT(r) AS count
    """,
    module=Module.KUBERNETES,
    maturity=Maturity.EXPERIMENTAL,
)

cis_k8s_5_1_4_pod_create_access = Rule(
    id="cis_k8s_5_1_4_pod_create_access",
    name="CIS K8s 5.1.4: Roles Granting Pod Creation",
    description=(
        "The ability to create pods in a namespace can provide opportunities for "
        "privilege escalation. Access to create new pods should be restricted to "
        "the smallest possible group of users."
    ),
    output_model=PodCreateAccessOutput,
    facts=(_k8s_pod_create_clusterroles, _k8s_pod_create_roles),
    tags=("rbac", "pods", "stride:elevation_of_privilege"),
    version="1.0.0",
    references=CIS_REFERENCES,
    frameworks=(
        Framework(
            name="CIS Kubernetes Benchmark",
            short_name="CIS",
            scope="kubernetes",
            revision="1.12",
            requirement="5.1.4",
        ),
    ),
)


# =============================================================================
# CIS K8s 5.1.5: Default service accounts not actively used
# Main node: KubernetesServiceAccount
# =============================================================================
class DefaultSaBindingsOutput(Finding):
    """Output model for default service account bindings check."""

    service_account_name: str | None = None
    namespace: str | None = None
    binding_name: str | None = None
    binding_type: str | None = None
    role_name: str | None = None
    cluster_name: str | None = None


_k8s_default_sa_cluster_role_bindings = Fact(
    id="k8s_default_sa_cluster_role_bindings",
    name="Kubernetes default service accounts with ClusterRoleBindings",
    description=(
        "Detects default service accounts that are bound to ClusterRoles "
        "via ClusterRoleBindings. Default service accounts should not have "
        "extra privileges to ensure proper auditability of workload permissions."
    ),
    cypher_query="""
    MATCH (cluster:KubernetesCluster)-[:RESOURCE]->(crb:KubernetesClusterRoleBinding)
          -[:SUBJECT]->(sa:KubernetesServiceAccount)
    WHERE sa.name = 'default'
    RETURN
        sa.name AS service_account_name,
        sa.namespace AS namespace,
        crb.name AS binding_name,
        'ClusterRoleBinding' AS binding_type,
        crb.role_name AS role_name,
        cluster.name AS cluster_name
    """,
    cypher_visual_query="""
    MATCH p=(cluster:KubernetesCluster)-[:RESOURCE]->(crb:KubernetesClusterRoleBinding)
          -[:SUBJECT]->(sa:KubernetesServiceAccount)
    WHERE sa.name = 'default'
    RETURN *
    """,
    cypher_count_query="""
    MATCH (sa:KubernetesServiceAccount)
    WHERE sa.name = 'default'
    RETURN COUNT(sa) AS count
    """,
    module=Module.KUBERNETES,
    maturity=Maturity.EXPERIMENTAL,
)

_k8s_default_sa_role_bindings = Fact(
    id="k8s_default_sa_role_bindings",
    name="Kubernetes default service accounts with RoleBindings",
    description=(
        "Detects default service accounts that are bound to Roles "
        "via RoleBindings. Default service accounts should not have "
        "extra privileges to ensure proper auditability of workload permissions."
    ),
    cypher_query="""
    MATCH (cluster:KubernetesCluster)-[:RESOURCE]->(rb:KubernetesRoleBinding)
          -[:SUBJECT]->(sa:KubernetesServiceAccount)
    WHERE sa.name = 'default'
    RETURN
        sa.name AS service_account_name,
        sa.namespace AS namespace,
        rb.name AS binding_name,
        'RoleBinding' AS binding_type,
        rb.role_name AS role_name,
        cluster.name AS cluster_name
    """,
    cypher_visual_query="""
    MATCH p=(cluster:KubernetesCluster)-[:RESOURCE]->(rb:KubernetesRoleBinding)
          -[:SUBJECT]->(sa:KubernetesServiceAccount)
    WHERE sa.name = 'default'
    RETURN *
    """,
    cypher_count_query="""
    MATCH (sa:KubernetesServiceAccount)
    WHERE sa.name = 'default'
    RETURN COUNT(sa) AS count
    """,
    module=Module.KUBERNETES,
    maturity=Maturity.EXPERIMENTAL,
)

cis_k8s_5_1_5_default_sa_bindings = Rule(
    id="cis_k8s_5_1_5_default_sa_bindings",
    name="CIS K8s 5.1.5: Default Service Accounts Actively Used",
    description=(
        "The default service account should not be used to ensure that rights "
        "granted to applications can be more easily audited and reviewed. "
        "Note: this rule checks for role bindings to the default SA but cannot "
        "verify automountServiceAccountToken settings (not ingested)."
    ),
    output_model=DefaultSaBindingsOutput,
    facts=(_k8s_default_sa_cluster_role_bindings, _k8s_default_sa_role_bindings),
    tags=("rbac", "service-accounts", "stride:elevation_of_privilege"),
    version="1.0.0",
    references=CIS_REFERENCES,
    frameworks=(
        Framework(
            name="CIS Kubernetes Benchmark",
            short_name="CIS",
            scope="kubernetes",
            revision="1.12",
            requirement="5.1.5",
        ),
    ),
)


# =============================================================================
# CIS K8s 5.1.7: Avoid use of system:masters group
# Main node: KubernetesClusterRoleBinding
# =============================================================================
class SystemMastersGroupOutput(Finding):
    """Output model for system:masters group usage check."""

    binding_name: str | None = None
    binding_type: str | None = None
    role_name: str | None = None
    cluster_name: str | None = None


_k8s_system_masters_cluster_role_bindings = Fact(
    id="k8s_system_masters_cluster_role_bindings",
    name="Kubernetes ClusterRoleBindings to system:masters group",
    description=(
        "Detects ClusterRoleBindings that grant access to the system:masters group. "
        "The system:masters group has unrestricted access hard-coded into the API server "
        "and cannot be reduced even if all bindings are removed."
    ),
    cypher_query="""
    MATCH (cluster:KubernetesCluster)-[:RESOURCE]->(crb:KubernetesClusterRoleBinding)
          -[:SUBJECT]->(g:KubernetesGroup)
    WHERE g.name = 'system:masters'
    RETURN
        crb.name AS binding_name,
        'ClusterRoleBinding' AS binding_type,
        crb.role_name AS role_name,
        cluster.name AS cluster_name
    """,
    cypher_visual_query="""
    MATCH p=(cluster:KubernetesCluster)-[:RESOURCE]->(crb:KubernetesClusterRoleBinding)
          -[:SUBJECT]->(g:KubernetesGroup)
    WHERE g.name = 'system:masters'
    RETURN *
    """,
    cypher_count_query="""
    MATCH (crb:KubernetesClusterRoleBinding)
    RETURN COUNT(crb) AS count
    """,
    asset_id_field="binding_name",
    module=Module.KUBERNETES,
    maturity=Maturity.EXPERIMENTAL,
)

_k8s_system_masters_role_bindings = Fact(
    id="k8s_system_masters_role_bindings",
    name="Kubernetes RoleBindings to system:masters group",
    description=(
        "Detects RoleBindings that grant access to the system:masters group. "
        "The system:masters group should not be used for namespace-scoped bindings."
    ),
    cypher_query="""
    MATCH (cluster:KubernetesCluster)-[:RESOURCE]->(rb:KubernetesRoleBinding)
          -[:SUBJECT]->(g:KubernetesGroup)
    WHERE g.name = 'system:masters'
    RETURN
        rb.name AS binding_name,
        'RoleBinding' AS binding_type,
        rb.role_name AS role_name,
        cluster.name AS cluster_name
    """,
    cypher_visual_query="""
    MATCH p=(cluster:KubernetesCluster)-[:RESOURCE]->(rb:KubernetesRoleBinding)
          -[:SUBJECT]->(g:KubernetesGroup)
    WHERE g.name = 'system:masters'
    RETURN *
    """,
    cypher_count_query="""
    MATCH (rb:KubernetesRoleBinding)
    RETURN COUNT(rb) AS count
    """,
    asset_id_field="binding_name",
    module=Module.KUBERNETES,
    maturity=Maturity.EXPERIMENTAL,
)

cis_k8s_5_1_7_system_masters_group = Rule(
    id="cis_k8s_5_1_7_system_masters_group",
    name="CIS K8s 5.1.7: system:masters Group Usage",
    description=(
        "The system:masters group has unrestricted access to the Kubernetes API "
        "hard-coded into the API server. An authenticated user who is a member of "
        "this group cannot have their access reduced. Avoid using this group."
    ),
    output_model=SystemMastersGroupOutput,
    facts=(
        _k8s_system_masters_cluster_role_bindings,
        _k8s_system_masters_role_bindings,
    ),
    tags=("rbac", "system-masters", "stride:elevation_of_privilege"),
    version="1.0.0",
    references=CIS_REFERENCES,
    frameworks=(
        Framework(
            name="CIS Kubernetes Benchmark",
            short_name="CIS",
            scope="kubernetes",
            revision="1.12",
            requirement="5.1.7",
        ),
    ),
)


# =============================================================================
# CIS K8s 5.1.8: Limit bind, impersonate, and escalate permissions
# Main node: KubernetesClusterRole / KubernetesRole
# =============================================================================
class EscalationPermissionsOutput(Finding):
    """Output model for escalation permissions check."""

    role_name: str | None = None
    role_type: str | None = None
    dangerous_verbs: str | None = None
    cluster_name: str | None = None


_k8s_escalation_clusterroles = Fact(
    id="k8s_escalation_clusterroles",
    name="Kubernetes ClusterRoles with bind/impersonate/escalate permissions",
    description=(
        "Detects ClusterRoles that grant bind, impersonate, or escalate permissions. "
        "Each of these allows privilege escalation beyond what was explicitly granted."
    ),
    cypher_query="""
    MATCH (cluster:KubernetesCluster)-[:RESOURCE]->(cr:KubernetesClusterRole)
    WHERE any(v IN cr.verbs WHERE v IN ['bind', 'impersonate', 'escalate', '*'])
      AND NOT cr.name STARTS WITH 'system:'
    RETURN
        cr.name AS role_name,
        'ClusterRole' AS role_type,
        [v IN cr.verbs WHERE v IN ['bind', 'impersonate', 'escalate', '*']] AS dangerous_verbs,
        cluster.name AS cluster_name
    """,
    cypher_visual_query="""
    MATCH p=(cluster:KubernetesCluster)-[:RESOURCE]->(cr:KubernetesClusterRole)
    WHERE any(v IN cr.verbs WHERE v IN ['bind', 'impersonate', 'escalate', '*'])
      AND NOT cr.name STARTS WITH 'system:'
    RETURN *
    """,
    cypher_count_query="""
    MATCH (cr:KubernetesClusterRole)
    WHERE NOT cr.name STARTS WITH 'system:'
    RETURN COUNT(cr) AS count
    """,
    module=Module.KUBERNETES,
    maturity=Maturity.EXPERIMENTAL,
)

_k8s_escalation_roles = Fact(
    id="k8s_escalation_roles",
    name="Kubernetes Roles with bind/impersonate/escalate permissions",
    description=(
        "Detects namespace-scoped Roles that grant bind, impersonate, or escalate permissions. "
        "Each of these allows privilege escalation beyond what was explicitly granted."
    ),
    cypher_query="""
    MATCH (cluster:KubernetesCluster)-[:RESOURCE]->(r:KubernetesRole)
    WHERE any(v IN r.verbs WHERE v IN ['bind', 'impersonate', 'escalate', '*'])
      AND NOT r.name STARTS WITH 'system:'
    RETURN
        r.name AS role_name,
        'Role' AS role_type,
        [v IN r.verbs WHERE v IN ['bind', 'impersonate', 'escalate', '*']] AS dangerous_verbs,
        cluster.name AS cluster_name
    """,
    cypher_visual_query="""
    MATCH p=(cluster:KubernetesCluster)-[:RESOURCE]->(r:KubernetesRole)
    WHERE any(v IN r.verbs WHERE v IN ['bind', 'impersonate', 'escalate', '*'])
      AND NOT r.name STARTS WITH 'system:'
    RETURN *
    """,
    cypher_count_query="""
    MATCH (r:KubernetesRole)
    WHERE NOT r.name STARTS WITH 'system:'
    RETURN COUNT(r) AS count
    """,
    module=Module.KUBERNETES,
    maturity=Maturity.EXPERIMENTAL,
)

cis_k8s_5_1_8_escalation_permissions = Rule(
    id="cis_k8s_5_1_8_escalation_permissions",
    name="CIS K8s 5.1.8: Bind/Impersonate/Escalate Permissions",
    description=(
        "Roles with impersonate, bind, or escalate permissions allow subjects to "
        "escalate their privileges beyond those explicitly granted. These permissions "
        "should be strictly limited."
    ),
    output_model=EscalationPermissionsOutput,
    facts=(_k8s_escalation_clusterroles, _k8s_escalation_roles),
    tags=("rbac", "escalation", "stride:elevation_of_privilege"),
    version="1.0.0",
    references=CIS_REFERENCES,
    frameworks=(
        Framework(
            name="CIS Kubernetes Benchmark",
            short_name="CIS",
            scope="kubernetes",
            revision="1.12",
            requirement="5.1.8",
        ),
    ),
)


# =============================================================================
# CIS K8s 5.1.9: Minimize access to create persistent volumes
# Main node: KubernetesClusterRole / KubernetesRole
# =============================================================================
class PvCreateAccessOutput(Finding):
    """Output model for PV creation access check."""

    role_name: str | None = None
    role_type: str | None = None
    cluster_name: str | None = None


_k8s_pv_create_clusterroles = Fact(
    id="k8s_pv_create_clusterroles",
    name="Kubernetes ClusterRoles granting persistent volume creation",
    description=(
        "Detects ClusterRoles that grant create access to persistent volumes. "
        "Creating PVs with hostPath can bypass Pod Security Admission controls "
        "and access sensitive host files."
    ),
    cypher_query="""
    MATCH (cluster:KubernetesCluster)-[:RESOURCE]->(cr:KubernetesClusterRole)
    WHERE ('persistentvolumes' IN cr.resources OR '*' IN cr.resources)
      AND any(v IN cr.verbs WHERE v IN ['create', '*'])
      AND NOT cr.name STARTS WITH 'system:'
    RETURN
        cr.name AS role_name,
        'ClusterRole' AS role_type,
        cluster.name AS cluster_name
    """,
    cypher_visual_query="""
    MATCH p=(cluster:KubernetesCluster)-[:RESOURCE]->(cr:KubernetesClusterRole)
    WHERE ('persistentvolumes' IN cr.resources OR '*' IN cr.resources)
      AND any(v IN cr.verbs WHERE v IN ['create', '*'])
      AND NOT cr.name STARTS WITH 'system:'
    RETURN *
    """,
    cypher_count_query="""
    MATCH (cr:KubernetesClusterRole)
    WHERE NOT cr.name STARTS WITH 'system:'
    RETURN COUNT(cr) AS count
    """,
    module=Module.KUBERNETES,
    maturity=Maturity.EXPERIMENTAL,
)

_k8s_pv_create_roles = Fact(
    id="k8s_pv_create_roles",
    name="Kubernetes Roles granting persistent volume creation",
    description=(
        "Detects namespace-scoped Roles that grant create access to persistent volumes. "
        "Creating PVs with hostPath can bypass Pod Security Admission controls "
        "and access sensitive host files."
    ),
    cypher_query="""
    MATCH (cluster:KubernetesCluster)-[:RESOURCE]->(r:KubernetesRole)
    WHERE ('persistentvolumes' IN r.resources OR '*' IN r.resources)
      AND any(v IN r.verbs WHERE v IN ['create', '*'])
      AND NOT r.name STARTS WITH 'system:'
    RETURN
        r.name AS role_name,
        'Role' AS role_type,
        cluster.name AS cluster_name
    """,
    cypher_visual_query="""
    MATCH p=(cluster:KubernetesCluster)-[:RESOURCE]->(r:KubernetesRole)
    WHERE ('persistentvolumes' IN r.resources OR '*' IN r.resources)
      AND any(v IN r.verbs WHERE v IN ['create', '*'])
      AND NOT r.name STARTS WITH 'system:'
    RETURN *
    """,
    cypher_count_query="""
    MATCH (r:KubernetesRole)
    WHERE NOT r.name STARTS WITH 'system:'
    RETURN COUNT(r) AS count
    """,
    module=Module.KUBERNETES,
    maturity=Maturity.EXPERIMENTAL,
)

cis_k8s_5_1_9_pv_create_access = Rule(
    id="cis_k8s_5_1_9_pv_create_access",
    name="CIS K8s 5.1.9: Roles Granting Persistent Volume Creation",
    description=(
        "The ability to create persistent volumes can provide privilege escalation "
        "via hostPath volumes, bypassing Pod Security Admission controls."
    ),
    output_model=PvCreateAccessOutput,
    facts=(_k8s_pv_create_clusterroles, _k8s_pv_create_roles),
    tags=("rbac", "persistent-volumes", "stride:elevation_of_privilege"),
    version="1.0.0",
    references=CIS_REFERENCES,
    frameworks=(
        Framework(
            name="CIS Kubernetes Benchmark",
            short_name="CIS",
            scope="kubernetes",
            revision="1.12",
            requirement="5.1.9",
        ),
    ),
)


# =============================================================================
# CIS K8s 5.1.10: Minimize access to the proxy sub-resource of nodes
# Main node: KubernetesClusterRole / KubernetesRole
# =============================================================================
class NodeProxyAccessOutput(Finding):
    """Output model for node proxy access check."""

    role_name: str | None = None
    role_type: str | None = None
    cluster_name: str | None = None


_k8s_node_proxy_clusterroles = Fact(
    id="k8s_node_proxy_clusterroles",
    name="Kubernetes ClusterRoles granting nodes/proxy access",
    description=(
        "Detects ClusterRoles that grant access to the proxy sub-resource of nodes. "
        "This provides direct access to the kubelet API, bypassing audit logging "
        "and admission control."
    ),
    cypher_query="""
    MATCH (cluster:KubernetesCluster)-[:RESOURCE]->(cr:KubernetesClusterRole)
    WHERE any(r IN cr.resources WHERE r IN ['nodes/proxy', '*'])
      AND NOT cr.name STARTS WITH 'system:'
    RETURN
        cr.name AS role_name,
        'ClusterRole' AS role_type,
        cluster.name AS cluster_name
    """,
    cypher_visual_query="""
    MATCH p=(cluster:KubernetesCluster)-[:RESOURCE]->(cr:KubernetesClusterRole)
    WHERE any(r IN cr.resources WHERE r IN ['nodes/proxy', '*'])
      AND NOT cr.name STARTS WITH 'system:'
    RETURN *
    """,
    cypher_count_query="""
    MATCH (cr:KubernetesClusterRole)
    WHERE NOT cr.name STARTS WITH 'system:'
    RETURN COUNT(cr) AS count
    """,
    module=Module.KUBERNETES,
    maturity=Maturity.EXPERIMENTAL,
)

cis_k8s_5_1_10_node_proxy_access = Rule(
    id="cis_k8s_5_1_10_node_proxy_access",
    name="CIS K8s 5.1.10: Node Proxy Sub-Resource Access",
    description=(
        "Access to the proxy sub-resource of nodes provides direct access to the "
        "kubelet API, bypassing audit logging and admission control. This access "
        "should be minimized."
    ),
    output_model=NodeProxyAccessOutput,
    facts=(_k8s_node_proxy_clusterroles,),
    tags=("rbac", "nodes", "kubelet", "stride:elevation_of_privilege"),
    version="1.0.0",
    references=CIS_REFERENCES,
    frameworks=(
        Framework(
            name="CIS Kubernetes Benchmark",
            short_name="CIS",
            scope="kubernetes",
            revision="1.12",
            requirement="5.1.10",
        ),
    ),
)


# =============================================================================
# CIS K8s 5.1.11: Minimize access to CSR approval
# Main node: KubernetesClusterRole
# =============================================================================
class CsrApprovalAccessOutput(Finding):
    """Output model for CSR approval access check."""

    role_name: str | None = None
    role_type: str | None = None
    cluster_name: str | None = None


_k8s_csr_approval_clusterroles = Fact(
    id="k8s_csr_approval_clusterroles",
    name="Kubernetes ClusterRoles granting CSR approval access",
    description=(
        "Detects ClusterRoles that grant update access to the approval sub-resource "
        "of CertificateSigningRequests. This can allow creation of new high-privileged "
        "client certificates for the Kubernetes API."
    ),
    cypher_query="""
    MATCH (cluster:KubernetesCluster)-[:RESOURCE]->(cr:KubernetesClusterRole)
    WHERE any(r IN cr.resources WHERE r IN ['certificatesigningrequests/approval', '*'])
      AND any(v IN cr.verbs WHERE v IN ['update', '*'])
      AND NOT cr.name STARTS WITH 'system:'
    RETURN
        cr.name AS role_name,
        'ClusterRole' AS role_type,
        cluster.name AS cluster_name
    """,
    cypher_visual_query="""
    MATCH p=(cluster:KubernetesCluster)-[:RESOURCE]->(cr:KubernetesClusterRole)
    WHERE any(r IN cr.resources WHERE r IN ['certificatesigningrequests/approval', '*'])
      AND any(v IN cr.verbs WHERE v IN ['update', '*'])
      AND NOT cr.name STARTS WITH 'system:'
    RETURN *
    """,
    cypher_count_query="""
    MATCH (cr:KubernetesClusterRole)
    WHERE NOT cr.name STARTS WITH 'system:'
    RETURN COUNT(cr) AS count
    """,
    module=Module.KUBERNETES,
    maturity=Maturity.EXPERIMENTAL,
)

cis_k8s_5_1_11_csr_approval_access = Rule(
    id="cis_k8s_5_1_11_csr_approval_access",
    name="CIS K8s 5.1.11: CSR Approval Sub-Resource Access",
    description=(
        "Users with access to approve CertificateSigningRequests can create new "
        "client certificates, effectively allowing creation of high-privileged user accounts."
    ),
    output_model=CsrApprovalAccessOutput,
    facts=(_k8s_csr_approval_clusterroles,),
    tags=("rbac", "certificates", "stride:elevation_of_privilege"),
    version="1.0.0",
    references=CIS_REFERENCES,
    frameworks=(
        Framework(
            name="CIS Kubernetes Benchmark",
            short_name="CIS",
            scope="kubernetes",
            revision="1.12",
            requirement="5.1.11",
        ),
    ),
)


# =============================================================================
# CIS K8s 5.1.12: Minimize access to webhook configuration objects
# Main node: KubernetesClusterRole / KubernetesRole
# =============================================================================
class WebhookConfigAccessOutput(Finding):
    """Output model for webhook configuration access check."""

    role_name: str | None = None
    role_type: str | None = None
    webhook_resources: str | None = None
    cluster_name: str | None = None


_k8s_webhook_config_clusterroles = Fact(
    id="k8s_webhook_config_clusterroles",
    name="Kubernetes ClusterRoles granting webhook configuration access",
    description=(
        "Detects ClusterRoles that grant create, update, or delete access to "
        "validatingwebhookconfigurations or mutatingwebhookconfigurations. "
        "This can allow reading or mutating any object admitted to the cluster."
    ),
    cypher_query="""
    MATCH (cluster:KubernetesCluster)-[:RESOURCE]->(cr:KubernetesClusterRole)
    WHERE any(r IN cr.resources WHERE r IN [
            'validatingwebhookconfigurations',
            'mutatingwebhookconfigurations',
            '*'
         ])
      AND any(v IN cr.verbs WHERE v IN ['create', 'update', 'patch', 'delete', '*'])
      AND NOT cr.name STARTS WITH 'system:'
    RETURN
        cr.name AS role_name,
        'ClusterRole' AS role_type,
        [r IN cr.resources WHERE r IN [
            'validatingwebhookconfigurations',
            'mutatingwebhookconfigurations'
        ]] AS webhook_resources,
        cluster.name AS cluster_name
    """,
    cypher_visual_query="""
    MATCH p=(cluster:KubernetesCluster)-[:RESOURCE]->(cr:KubernetesClusterRole)
    WHERE any(r IN cr.resources WHERE r IN [
            'validatingwebhookconfigurations',
            'mutatingwebhookconfigurations',
            '*'
         ])
      AND any(v IN cr.verbs WHERE v IN ['create', 'update', 'patch', 'delete', '*'])
      AND NOT cr.name STARTS WITH 'system:'
    RETURN *
    """,
    cypher_count_query="""
    MATCH (cr:KubernetesClusterRole)
    WHERE NOT cr.name STARTS WITH 'system:'
    RETURN COUNT(cr) AS count
    """,
    module=Module.KUBERNETES,
    maturity=Maturity.EXPERIMENTAL,
)

cis_k8s_5_1_12_webhook_config_access = Rule(
    id="cis_k8s_5_1_12_webhook_config_access",
    name="CIS K8s 5.1.12: Webhook Configuration Access",
    description=(
        "Users with rights to create, modify, or delete webhook configurations "
        "can control webhooks that read or mutate any object admitted to the cluster, "
        "potentially allowing privilege escalation."
    ),
    output_model=WebhookConfigAccessOutput,
    facts=(_k8s_webhook_config_clusterroles,),
    tags=("rbac", "webhooks", "stride:elevation_of_privilege", "stride:tampering"),
    version="1.0.0",
    references=CIS_REFERENCES,
    frameworks=(
        Framework(
            name="CIS Kubernetes Benchmark",
            short_name="CIS",
            scope="kubernetes",
            revision="1.12",
            requirement="5.1.12",
        ),
    ),
)


# =============================================================================
# CIS K8s 5.1.13: Minimize access to service account token creation
# Main node: KubernetesClusterRole
# =============================================================================
class SaTokenCreationAccessOutput(Finding):
    """Output model for SA token creation access check."""

    role_name: str | None = None
    role_type: str | None = None
    cluster_name: str | None = None


_k8s_sa_token_creation_clusterroles = Fact(
    id="k8s_sa_token_creation_clusterroles",
    name="Kubernetes ClusterRoles granting service account token creation",
    description=(
        "Detects ClusterRoles that grant create access to the token sub-resource "
        "of serviceaccounts. This can allow creation of long-lived privileged "
        "credentials that persist even after the user's account is revoked."
    ),
    cypher_query="""
    MATCH (cluster:KubernetesCluster)-[:RESOURCE]->(cr:KubernetesClusterRole)
    WHERE any(r IN cr.resources WHERE r IN ['serviceaccounts/token', '*'])
      AND any(v IN cr.verbs WHERE v IN ['create', '*'])
      AND NOT cr.name STARTS WITH 'system:'
    RETURN
        cr.name AS role_name,
        'ClusterRole' AS role_type,
        cluster.name AS cluster_name
    """,
    cypher_visual_query="""
    MATCH p=(cluster:KubernetesCluster)-[:RESOURCE]->(cr:KubernetesClusterRole)
    WHERE any(r IN cr.resources WHERE r IN ['serviceaccounts/token', '*'])
      AND any(v IN cr.verbs WHERE v IN ['create', '*'])
      AND NOT cr.name STARTS WITH 'system:'
    RETURN *
    """,
    cypher_count_query="""
    MATCH (cr:KubernetesClusterRole)
    WHERE NOT cr.name STARTS WITH 'system:'
    RETURN COUNT(cr) AS count
    """,
    module=Module.KUBERNETES,
    maturity=Maturity.EXPERIMENTAL,
)

cis_k8s_5_1_13_sa_token_creation = Rule(
    id="cis_k8s_5_1_13_sa_token_creation",
    name="CIS K8s 5.1.13: Service Account Token Creation Access",
    description=(
        "Users with rights to create service account tokens can create long-lived "
        "privileged credentials that persist even after the user's account is revoked."
    ),
    output_model=SaTokenCreationAccessOutput,
    facts=(_k8s_sa_token_creation_clusterroles,),
    tags=("rbac", "service-accounts", "tokens", "stride:elevation_of_privilege"),
    version="1.0.0",
    references=CIS_REFERENCES,
    frameworks=(
        Framework(
            name="CIS Kubernetes Benchmark",
            short_name="CIS",
            scope="kubernetes",
            revision="1.12",
            requirement="5.1.13",
        ),
    ),
)
