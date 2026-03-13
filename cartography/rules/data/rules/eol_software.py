from cartography.rules.spec.model import Fact
from cartography.rules.spec.model import Finding
from cartography.rules.spec.model import Maturity
from cartography.rules.spec.model import Module
from cartography.rules.spec.model import Rule
from cartography.rules.spec.model import RuleReference

_OLDEST_SUPPORTED_UPSTREAM_KUBERNETES_MINOR = 33
_OLDEST_SUPPORTED_EKS_KUBERNETES_MINOR = 29
_AMAZON_LINUX_2_EOL_DATE = "2026-06-30"

EOL_SOFTWARE_REFERENCES = [
    RuleReference(
        text="Kubernetes Version Skew Policy",
        url="https://kubernetes.io/releases/version-skew-policy/",
    ),
    RuleReference(
        text="Kubernetes Releases",
        url="https://kubernetes.io/releases/",
    ),
    RuleReference(
        text="Amazon EKS Kubernetes version lifecycle",
        url="https://docs.aws.amazon.com/eks/latest/userguide/kubernetes-versions.html",
    ),
    RuleReference(
        text="Amazon Linux 2 release notes",
        url="https://docs.aws.amazon.com/AL2/latest/relnotes/relnotes-al2.html",
    ),
    RuleReference(
        text="Amazon Linux 2023 release cadence",
        url="https://docs.aws.amazon.com/linux/al2023/ug/release-cadence.html",
    ),
    RuleReference(
        text="AWS Systems Manager InstanceInformation API",
        url="https://docs.aws.amazon.com/systems-manager/latest/APIReference/API_InstanceInformation.html",
    ),
]


def _build_ec2_instance_amazon_linux_2_eol_query(
    current_date_expression: str = "date()",
) -> str:
    return f"""
    MATCH (ec2:EC2Instance)-[:HAS_INFORMATION]->(ssm:SSMInstanceInformation)
    WHERE toLower(trim(coalesce(ssm.platform_name, ''))) = 'amazon linux'
      AND trim(toString(ssm.platform_version)) = '2'
      AND {current_date_expression} > date('{_AMAZON_LINUX_2_EOL_DATE}')
    RETURN ec2.id AS asset_id,
           coalesce(ec2.instanceid, ec2.id) AS asset_name,
           'EC2Instance' AS asset_type,
           'amazon-linux' AS software_name,
           trim(toString(ssm.platform_version)) AS software_version,
           2 AS software_major,
           NULL AS software_minor,
           coalesce(ssm.region, ec2.region) AS location,
           'vendor' AS support_basis,
           'eol' AS support_status
    ORDER BY asset_name
    """


_eks_cluster_kubernetes_version_eol = Fact(
    id="eks_cluster_kubernetes_version_eol",
    name="EKS clusters running end-of-life Kubernetes versions",
    description=(
        "Detects EKS clusters running Kubernetes minor versions that are no longer "
        "supported by Amazon EKS. As of 2026-03-10, EKS-supported Kubernetes "
        "minors are 1.34, 1.33, 1.32, 1.31, 1.30, and 1.29."
    ),
    cypher_query=f"""
    MATCH (e:EKSCluster)
    WITH e,
         CASE
             WHEN e.version IS NULL OR size(split(toString(e.version), '.')) < 2 THEN NULL
             ELSE toInteger(split(split(toString(e.version), '.')[1], '-')[0])
         END AS kubernetes_minor
    WHERE kubernetes_minor IS NOT NULL
      AND kubernetes_minor < {_OLDEST_SUPPORTED_EKS_KUBERNETES_MINOR}
    RETURN e.id AS asset_id,
           e.name AS asset_name,
           'EKSCluster' AS asset_type,
           'kubernetes' AS software_name,
           toString(e.version) AS software_version,
           1 AS software_major,
           kubernetes_minor AS software_minor,
           e.region AS location,
           'provider' AS support_basis,
           'eol' AS support_status
    ORDER BY asset_name
    """,
    cypher_visual_query=f"""
    MATCH account_path=(a:AWSAccount)-[:RESOURCE]->(e:EKSCluster)
    WITH account_path, e,
         CASE
             WHEN e.version IS NULL OR size(split(toString(e.version), '.')) < 2 THEN NULL
             ELSE toInteger(split(split(toString(e.version), '.')[1], '-')[0])
         END AS kubernetes_minor
    WHERE kubernetes_minor IS NOT NULL
      AND kubernetes_minor < {_OLDEST_SUPPORTED_EKS_KUBERNETES_MINOR}
    OPTIONAL MATCH worker_path=(ec2:EC2Instance)-[:MEMBER_OF_EKS_CLUSTER]->(e)
    WITH account_path, e, head(collect(worker_path)) AS worker_path
    RETURN e AS cluster, account_path, worker_path
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
        "represented as an EKSCluster, it is excluded so managed clusters are "
        "evaluated against the EKS provider lifecycle instead of upstream support."
    ),
    cypher_query=f"""
    MATCH (k:KubernetesCluster)
    WITH k,
         CASE
             WHEN k.version_minor IS NULL THEN NULL
             ELSE toInteger(replace(toString(k.version_minor), '+', ''))
         END AS kubernetes_minor
    WHERE kubernetes_minor IS NOT NULL
      AND kubernetes_minor < {_OLDEST_SUPPORTED_UPSTREAM_KUBERNETES_MINOR}
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
           NULL AS location,
           'upstream' AS support_basis,
           'eol' AS support_status
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
      AND kubernetes_minor < {_OLDEST_SUPPORTED_UPSTREAM_KUBERNETES_MINOR}
      AND NOT EXISTS {{
          MATCH (e:EKSCluster)
          WHERE e.id = k.external_id
             OR e.name = k.external_id
             OR (k.api_server_url IS NOT NULL AND e.endpoint = k.api_server_url)
      }}
    OPTIONAL MATCH workload_path=(k)-[:RESOURCE]->(svc:KubernetesService)-[:TARGETS]->(pod:KubernetesPod)
    WITH k, head(collect(workload_path)) AS workload_path
    OPTIONAL MATCH resource_path=(k)-[:RESOURCE]->(r)
    WITH k, workload_path, head(collect(resource_path)) AS resource_path
    RETURN k AS cluster, workload_path, resource_path
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

_ec2_instance_amazon_linux_2_eol = Fact(
    id="ec2_instance_amazon_linux_2_eol",
    name="EC2 instances running end-of-life Amazon Linux 2",
    description=(
        "Detects EC2 instances whose AWS Systems Manager InstanceInformation reports "
        "Amazon Linux version 2 after the Amazon Linux 2 end-of-life date of "
        "2026-06-30."
    ),
    cypher_query=_build_ec2_instance_amazon_linux_2_eol_query(),
    cypher_visual_query=f"""
    MATCH (ec2:EC2Instance)-[:HAS_INFORMATION]->(ssm:SSMInstanceInformation)
    WHERE toLower(trim(coalesce(ssm.platform_name, ''))) = 'amazon linux'
      AND trim(toString(ssm.platform_version)) = '2'
      AND date() > date('{_AMAZON_LINUX_2_EOL_DATE}')
    OPTIONAL MATCH p=(a:AWSAccount)-[:RESOURCE]->(ec2)
    RETURN *
    """,
    cypher_count_query=f"""
    MATCH (ec2:EC2Instance)-[:HAS_INFORMATION]->(ssm:SSMInstanceInformation)
    WHERE toLower(trim(coalesce(ssm.platform_name, ''))) = 'amazon linux'
      AND trim(toString(ssm.platform_version)) = '2'
      AND date() > date('{_AMAZON_LINUX_2_EOL_DATE}')
    RETURN COUNT(ec2) AS count
    """,
    asset_id_field="asset_id",
    module=Module.AWS,
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
    support_basis: str | None = None
    support_status: str | None = None


eol_software = Rule(
    id="eol_software",
    name="End-of-Life Software",
    description=(
        "Detects infrastructure running end-of-life software versions. "
        "The initial coverage flags raw Kubernetes clusters using the upstream "
        "Kubernetes support window and EKS clusters using the Amazon EKS "
        "provider lifecycle. It also flags EC2 instances that AWS SSM reports "
        "as running Amazon Linux 2 after the vendor end-of-life date."
    ),
    output_model=EOLSoftwareOutput,
    facts=(
        _eks_cluster_kubernetes_version_eol,
        _kubernetes_cluster_kubernetes_version_eol,
        _ec2_instance_amazon_linux_2_eol,
    ),
    tags=(
        "infrastructure",
        "kubernetes",
        "ec2",
        "operating_system",
        "lifecycle",
        "compliance",
    ),
    version="0.2.0",
    references=EOL_SOFTWARE_REFERENCES,
)
