from cartography.rules.spec.model import Fact
from cartography.rules.spec.model import Finding
from cartography.rules.spec.model import Maturity
from cartography.rules.spec.model import Module
from cartography.rules.spec.model import Rule
from cartography.rules.spec.model import RuleReference

_OLDEST_SUPPORTED_KUBERNETES_MINOR = 33

KUBERNETES_EOL_REFERENCES = [
    RuleReference(
        text="Kubernetes Version Skew Policy",
        url="https://kubernetes.io/releases/version-skew-policy/",
    ),
    RuleReference(
        text="Kubernetes Releases",
        url="https://kubernetes.io/releases/",
    ),
]

_eks_cluster_kubernetes_version_eol = Fact(
    id="eks_cluster_kubernetes_version_eol",
    name="EKS clusters running end-of-life Kubernetes versions",
    description=(
        "Detects EKS clusters running Kubernetes minor versions older than the "
        "current upstream support window. As of 2026-03-10, upstream-supported "
        "Kubernetes minors are 1.35, 1.34, and 1.33."
    ),
    cypher_query=f"""
    MATCH (e:EKSCluster)
    WITH e,
         CASE
             WHEN e.version IS NULL OR size(split(toString(e.version), '.')) < 2 THEN NULL
             ELSE toInteger(split(split(toString(e.version), '.')[1], '-')[0])
         END AS kubernetes_minor
    WHERE kubernetes_minor IS NOT NULL
      AND kubernetes_minor < {_OLDEST_SUPPORTED_KUBERNETES_MINOR}
    RETURN e.id AS asset_id,
           e.name AS asset_name,
           'EKSCluster' AS asset_type,
           'kubernetes' AS software_name,
           toString(e.version) AS software_version,
           1 AS software_major,
           kubernetes_minor AS software_minor,
           e.region AS location
    ORDER BY asset_name
    """,
    cypher_visual_query=f"""
    MATCH (e:EKSCluster)
    WITH e,
         CASE
             WHEN e.version IS NULL OR size(split(toString(e.version), '.')) < 2 THEN NULL
             ELSE toInteger(split(split(toString(e.version), '.')[1], '-')[0])
         END AS kubernetes_minor
    WHERE kubernetes_minor IS NOT NULL
      AND kubernetes_minor < {_OLDEST_SUPPORTED_KUBERNETES_MINOR}
    OPTIONAL MATCH p=(a:AWSAccount)-[:RESOURCE]->(e)
    RETURN *
    """,
    cypher_count_query="""
    MATCH (e:EKSCluster)
    RETURN COUNT(e) AS count
    """,
    asset_id_field="asset_id",
    module=Module.AWS,
    maturity=Maturity.EXPERIMENTAL,
)

_kubernetes_cluster_kubernetes_version_eol = Fact(
    id="kubernetes_cluster_kubernetes_version_eol",
    name="Kubernetes clusters running end-of-life Kubernetes versions",
    description=(
        "Detects Kubernetes clusters running end-of-life minor versions. "
        "If a native KubernetesCluster is the same EKS-backed cluster already "
        "represented as an EKSCluster, it is excluded to avoid double counting."
    ),
    cypher_query=f"""
    MATCH (k:KubernetesCluster)
    WITH k,
         CASE
             WHEN k.version_minor IS NULL THEN NULL
             ELSE toInteger(replace(toString(k.version_minor), '+', ''))
         END AS kubernetes_minor
    WHERE kubernetes_minor IS NOT NULL
      AND kubernetes_minor < {_OLDEST_SUPPORTED_KUBERNETES_MINOR}
      AND NOT EXISTS {{
          MATCH (e:EKSCluster)
          WHERE e.id = k.external_id
             OR e.name = k.external_id
             OR (k.api_server_url IS NOT NULL AND e.endpoint = k.api_server_url)
      }}
    RETURN k.id AS asset_id,
           k.name AS asset_name,
           'KubernetesCluster' AS asset_type,
           'kubernetes' AS software_name,
           toString(k.version) AS software_version,
           1 AS software_major,
           kubernetes_minor AS software_minor,
           NULL AS location
    ORDER BY asset_name
    """,
    cypher_visual_query=f"""
    MATCH (k:KubernetesCluster)
    WITH k,
         CASE
             WHEN k.version_minor IS NULL THEN NULL
             ELSE toInteger(replace(toString(k.version_minor), '+', ''))
         END AS kubernetes_minor
    WHERE kubernetes_minor IS NOT NULL
      AND kubernetes_minor < {_OLDEST_SUPPORTED_KUBERNETES_MINOR}
      AND NOT EXISTS {{
          MATCH (e:EKSCluster)
          WHERE e.id = k.external_id
             OR e.name = k.external_id
             OR (k.api_server_url IS NOT NULL AND e.endpoint = k.api_server_url)
      }}
    OPTIONAL MATCH p=(k)-[:RESOURCE]->(r)
    RETURN *
    """,
    cypher_count_query="""
    MATCH (k:KubernetesCluster)
    WHERE NOT EXISTS {
        MATCH (e:EKSCluster)
        WHERE e.id = k.external_id
           OR e.name = k.external_id
           OR (k.api_server_url IS NOT NULL AND e.endpoint = k.api_server_url)
    }
    RETURN COUNT(k) AS count
    """,
    asset_id_field="asset_id",
    module=Module.KUBERNETES,
    maturity=Maturity.EXPERIMENTAL,
)


class EOLSoftwareOutput(Finding):
    asset_id: str | None = None
    asset_name: str | None = None
    asset_type: str | None = None
    software_name: str | None = None
    software_version: str | None = None
    software_major: int | None = None
    software_minor: int | None = None
    location: str | None = None


eol_software = Rule(
    id="eol_software",
    name="End-of-Life Software",
    description=(
        "Detects infrastructure running end-of-life software versions. "
        "The initial coverage flags Kubernetes and EKS clusters on "
        "upstream-unsupported Kubernetes minors."
    ),
    output_model=EOLSoftwareOutput,
    facts=(
        _eks_cluster_kubernetes_version_eol,
        _kubernetes_cluster_kubernetes_version_eol,
    ),
    tags=(
        "infrastructure",
        "kubernetes",
        "lifecycle",
        "compliance",
    ),
    version="0.1.0",
    references=KUBERNETES_EOL_REFERENCES,
)
