from cartography.rules.data.frameworks.iso27001 import iso27001_annex_a
from cartography.rules.spec.model import Fact
from cartography.rules.spec.model import Finding
from cartography.rules.spec.model import Maturity
from cartography.rules.spec.model import Module
from cartography.rules.spec.model import Rule
from cartography.rules.spec.model import RuleReference

_OLDEST_SUPPORTED_UPSTREAM_KUBERNETES_MINOR = 33
# AWS EKS supports 1.35 / 1.34 / 1.33 in standard support and 1.32 / 1.31 /
# 1.30 in extended support as of 2026-05; 1.29 is no longer covered.
# https://docs.aws.amazon.com/eks/latest/userguide/kubernetes-versions.html
_OLDEST_SUPPORTED_EKS_KUBERNETES_MINOR = 30
_OLDEST_SUPPORTED_GKE_KUBERNETES_MINOR = 30
# Microsoft AKS supported versions table starts at 1.33 as of 2026-05; 1.32
# reached community EOL in March 2026. See:
# https://learn.microsoft.com/en-us/azure/aks/supported-kubernetes-versions
_OLDEST_SUPPORTED_AKS_KUBERNETES_MINOR = 33
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
        text="GKE release schedule and support",
        url="https://cloud.google.com/kubernetes-engine/docs/release-schedule",
    ),
    RuleReference(
        text="AKS supported Kubernetes versions",
        url="https://learn.microsoft.com/en-us/azure/aks/supported-kubernetes-versions",
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
    RuleReference(
        text="Ingress NGINX Retirement",
        url="https://kubernetes.io/blog/2025/11/11/ingress-nginx-retirement/",
    ),
    RuleReference(
        text="Ingress NGINX retirement statement",
        url="https://kubernetes.io/blog/2026/01/29/ingress-nginx-statement/",
    ),
    RuleReference(
        text="kubernetes/ingress-nginx archived repository",
        url="https://github.com/kubernetes/ingress-nginx",
    ),
]


def _build_ec2_instance_amazon_linux_2_eol_query(
    current_date_expression: str = "date()",
) -> str:
    return f"""
    MATCH (ec2:AWSEC2Instance)-[:HAS_INFORMATION]->(ssm:AWSSSMInstanceInformation)
    WHERE toLower(trim(coalesce(ssm.platform_name, ''))) = 'amazon linux'
      AND trim(toString(ssm.platform_version)) = '2'
      AND {current_date_expression} > date('{_AMAZON_LINUX_2_EOL_DATE}')
    RETURN ec2.id AS asset_id,
           coalesce(ec2.instanceid, ec2.id) AS asset_name,
           'AWSEC2Instance' AS asset_type,
           'amazon-linux' AS software_name,
           trim(toString(ssm.platform_version)) AS software_version,
           2 AS software_major,
           NULL AS software_minor,
           coalesce(ssm.region, ec2.region) AS location,
           'vendor' AS support_basis,
           'eol' AS support_status
    ORDER BY asset_name
    """


def _build_kubernetes_ingress_nginx_eol_query() -> str:
    return """
    MATCH (cluster:KubernetesCluster)-[:RESOURCE]->(pod:KubernetesPod)
    CALL {
        WITH pod
        MATCH (container:KubernetesContainer)-[:WORKLOAD_PARENT]->(pod)
        RETURN container
        UNION
        WITH pod
        MATCH (pod)-[:CONTAINS]->(container:KubernetesContainer)
        RETURN container
    }
    WITH DISTINCT cluster, pod, container
    WITH cluster, pod, container,
         replace(toLower(coalesce(pod.labels, '')), ' ', '') AS labels_compacted,
         toLower(coalesce(container.image, '')) AS image
    WITH cluster, pod, container, labels_compacted, image,
         labels_compacted CONTAINS '"app.kubernetes.io/name":"ingress-nginx"'
             AND labels_compacted CONTAINS '"app.kubernetes.io/component":"controller"'
             AS has_controller_labels,
         image CONTAINS '/ingress-nginx/controller:' AS has_controller_image
    WHERE has_controller_labels OR has_controller_image
    WITH cluster, pod, container, labels_compacted, image,
         CASE
             WHEN labels_compacted CONTAINS '"app.kubernetes.io/instance":"'
             THEN split(split(labels_compacted, '"app.kubernetes.io/instance":"')[1], '"')[0]
             ELSE 'ingress-nginx'
         END AS controller_instance,
         CASE
             WHEN labels_compacted CONTAINS '"app.kubernetes.io/version":"'
             THEN split(split(labels_compacted, '"app.kubernetes.io/version":"')[1], '"')[0]
             WHEN image CONTAINS '/ingress-nginx/controller:'
             THEN split(split(image, '/ingress-nginx/controller:')[1], '@')[0]
             ELSE NULL
         END AS software_version_raw
    WITH cluster, pod, container, controller_instance,
         CASE
             WHEN software_version_raw STARTS WITH 'v'
             THEN substring(software_version_raw, 1)
             ELSE software_version_raw
         END AS software_version
    WITH cluster,
         coalesce(pod.namespace, container.namespace, 'default') AS namespace,
         controller_instance,
         software_version,
         CASE
             WHEN software_version IS NULL OR size(split(software_version, '.')) < 1 THEN NULL
             ELSE toInteger(split(software_version, '.')[0])
         END AS software_major,
         CASE
             WHEN software_version IS NULL OR size(split(software_version, '.')) < 2 THEN NULL
             ELSE toInteger(split(split(software_version, '.')[1], '-')[0])
         END AS software_minor
    WITH DISTINCT cluster, namespace, controller_instance,
                  software_version, software_major, software_minor
    RETURN cluster.id AS cluster_id,
           coalesce(cluster.id, cluster.name, 'unknown-cluster')
               + '/namespaces/' + namespace
               + '/ingress-controllers/' + controller_instance
               + '/' + coalesce(software_version, 'unknown') AS asset_id,
           coalesce(cluster.name, cluster.id, 'unknown-cluster')
               + '/' + namespace
               + '/' + controller_instance AS asset_name,
           'KubernetesIngressController' AS asset_type,
           'ingress-nginx' AS software_name,
           software_version AS software_version,
           software_major AS software_major,
           software_minor AS software_minor,
           NULL AS location,
           'upstream' AS support_basis,
           'eol' AS support_status
    ORDER BY asset_name, software_version
    """


_eks_cluster_kubernetes_version_eol = Fact(
    id="eks_cluster_kubernetes_version_eol",
    name="EKS clusters running end-of-life Kubernetes versions",
    description=(
        "Detects EKS clusters running Kubernetes minor versions that are no "
        "longer supported by Amazon EKS. As of 2026-05, EKS standard support "
        "covers 1.35 / 1.34 / 1.33 and extended support covers 1.32 / 1.31 / "
        "1.30; 1.29 and earlier are EOL."
    ),
    cypher_query=f"""
    MATCH (e:AWSEKSCluster)
    WITH e,
         CASE
             WHEN e.version IS NULL OR size(split(toString(e.version), '.')) < 2 THEN NULL
             ELSE toInteger(split(split(toString(e.version), '.')[1], '-')[0])
         END AS kubernetes_minor
    WHERE kubernetes_minor IS NOT NULL
      AND kubernetes_minor < {_OLDEST_SUPPORTED_EKS_KUBERNETES_MINOR}
    RETURN e.id AS asset_id,
           e.name AS asset_name,
           'AWSEKSCluster' AS asset_type,
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
    MATCH account_path=(a:AWSAccount)-[:RESOURCE]->(e:AWSEKSCluster)
    WITH account_path, e,
         CASE
             WHEN e.version IS NULL OR size(split(toString(e.version), '.')) < 2 THEN NULL
             ELSE toInteger(split(split(toString(e.version), '.')[1], '-')[0])
         END AS kubernetes_minor
    WHERE kubernetes_minor IS NOT NULL
      AND kubernetes_minor < {_OLDEST_SUPPORTED_EKS_KUBERNETES_MINOR}
    OPTIONAL MATCH worker_path=(ec2:AWSEC2Instance)-[:MEMBER_OF_EKS_CLUSTER]->(e)
    WITH account_path, e, head(collect(worker_path)) AS worker_path
    RETURN e AS cluster, account_path, worker_path
    """,
    cypher_count_query="""
    MATCH (e:AWSEKSCluster)
    RETURN COUNT(e) AS count
    """,
    asset_label="AWSEKSCluster",
    asset_id_field="asset_id",
    identity_fields=("asset_id",),
    module=Module.AWS,
    maturity=Maturity.EXPERIMENTAL,
)

_gke_cluster_kubernetes_version_eol = Fact(
    id="gke_cluster_kubernetes_version_eol",
    name="GKE clusters running end-of-life Kubernetes versions",
    description=(
        "Detects GKE clusters whose control-plane (current_master_version) "
        f"runs a Kubernetes minor older than {_OLDEST_SUPPORTED_GKE_KUBERNETES_MINOR}, "
        "the oldest minor still supported by Google's release schedule."
    ),
    cypher_query=f"""
    MATCH (g:GKECluster)
    WITH g,
         CASE
             WHEN g.current_master_version IS NULL
                  OR size(split(toString(g.current_master_version), '.')) < 2 THEN NULL
             ELSE toInteger(split(split(toString(g.current_master_version), '.')[1], '-')[0])
         END AS kubernetes_minor
    WHERE kubernetes_minor IS NOT NULL
      AND kubernetes_minor < {_OLDEST_SUPPORTED_GKE_KUBERNETES_MINOR}
    RETURN g.id AS asset_id,
           g.name AS asset_name,
           'GKECluster' AS asset_type,
           'kubernetes' AS software_name,
           toString(g.current_master_version) AS software_version,
           1 AS software_major,
           kubernetes_minor AS software_minor,
           g.location AS location,
           'provider' AS support_basis,
           'eol' AS support_status
    ORDER BY asset_name
    """,
    cypher_visual_query=f"""
    MATCH project_path=(p:GCPProject)-[:RESOURCE]->(g:GKECluster)
    WITH project_path, g,
         CASE
             WHEN g.current_master_version IS NULL
                  OR size(split(toString(g.current_master_version), '.')) < 2 THEN NULL
             ELSE toInteger(split(split(toString(g.current_master_version), '.')[1], '-')[0])
         END AS kubernetes_minor
    WHERE kubernetes_minor IS NOT NULL
      AND kubernetes_minor < {_OLDEST_SUPPORTED_GKE_KUBERNETES_MINOR}
    RETURN g AS cluster, project_path
    """,
    cypher_count_query="""
    MATCH (g:GKECluster)
    RETURN COUNT(g) AS count
    """,
    asset_label="GKECluster",
    asset_id_field="asset_id",
    identity_fields=("asset_id",),
    module=Module.GCP,
    maturity=Maturity.EXPERIMENTAL,
)


_aks_cluster_kubernetes_version_eol = Fact(
    id="aks_cluster_kubernetes_version_eol",
    name="AKS clusters outside Microsoft's standard-support window",
    description=(
        "Detects AKS clusters whose kubernetes_version runs a minor older "
        f"than {_OLDEST_SUPPORTED_AKS_KUBERNETES_MINOR}, the oldest minor "
        "still in Microsoft's standard AKS support window. Microsoft also "
        "offers a paid Long-Term Support (LTS) tier on selected minors "
        "(e.g. 1.32 LTS to March 2027). The current AKS data model does "
        "not expose an LTS / supportTier flag, so clusters enrolled in "
        "LTS may show up here as a false positive: treat the finding as "
        "'standard-support EOL' rather than 'unsupported by the provider'."
    ),
    cypher_query=f"""
    MATCH (a:AzureKubernetesCluster)
    WITH a,
         CASE
             WHEN a.kubernetes_version IS NULL
                  OR size(split(toString(a.kubernetes_version), '.')) < 2 THEN NULL
             ELSE toInteger(split(split(toString(a.kubernetes_version), '.')[1], '-')[0])
         END AS kubernetes_minor
    WHERE kubernetes_minor IS NOT NULL
      AND kubernetes_minor < {_OLDEST_SUPPORTED_AKS_KUBERNETES_MINOR}
    RETURN a.id AS asset_id,
           a.name AS asset_name,
           'AzureKubernetesCluster' AS asset_type,
           'kubernetes' AS software_name,
           toString(a.kubernetes_version) AS software_version,
           1 AS software_major,
           kubernetes_minor AS software_minor,
           a.location AS location,
           'provider' AS support_basis,
           'standard-support-eol' AS support_status
    ORDER BY asset_name
    """,
    cypher_visual_query=f"""
    MATCH sub_path=(s:AzureSubscription)-[:RESOURCE]->(a:AzureKubernetesCluster)
    WITH sub_path, a,
         CASE
             WHEN a.kubernetes_version IS NULL
                  OR size(split(toString(a.kubernetes_version), '.')) < 2 THEN NULL
             ELSE toInteger(split(split(toString(a.kubernetes_version), '.')[1], '-')[0])
         END AS kubernetes_minor
    WHERE kubernetes_minor IS NOT NULL
      AND kubernetes_minor < {_OLDEST_SUPPORTED_AKS_KUBERNETES_MINOR}
    RETURN a AS cluster, sub_path
    """,
    cypher_count_query="""
    MATCH (a:AzureKubernetesCluster)
    RETURN COUNT(a) AS count
    """,
    asset_label="AzureKubernetesCluster",
    asset_id_field="asset_id",
    identity_fields=("asset_id",),
    module=Module.AZURE,
    maturity=Maturity.EXPERIMENTAL,
)


_kubernetes_cluster_kubernetes_version_eol = Fact(
    id="kubernetes_cluster_kubernetes_version_eol",
    name="Kubernetes clusters running end-of-life Kubernetes versions",
    description=(
        "Detects Kubernetes clusters running end-of-life minor versions. "
        "If a native KubernetesCluster is the same EKS-backed cluster already "
        "represented as an AWSEKSCluster, it is excluded so managed clusters are "
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
          MATCH (e:AWSEKSCluster)
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
          MATCH (e:AWSEKSCluster)
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
        MATCH (e:AWSEKSCluster)
        WHERE e.id = k.external_id
           OR e.name = k.external_id
           OR (k.api_server_url IS NOT NULL AND e.endpoint = k.api_server_url)
    }
    RETURN COUNT(k) AS count
    """,
    asset_label="KubernetesCluster",
    asset_id_field="asset_id",
    identity_fields=("asset_id",),
    module=Module.KUBERNETES,
    maturity=Maturity.EXPERIMENTAL,
)


_kubernetes_ingress_nginx_controller_eol = Fact(
    id="kubernetes_ingress_nginx_controller_eol",
    name="Kubernetes clusters running retired ingress-nginx controllers",
    description=(
        "Detects deployed Kubernetes ingress-nginx controller workloads now "
        "that the upstream ingress-nginx project has been retired and no "
        "longer receives bug fixes or security updates."
    ),
    cypher_query=_build_kubernetes_ingress_nginx_eol_query(),
    cypher_visual_query="""
    MATCH resource_path=(cluster:KubernetesCluster)-[:RESOURCE]->(pod:KubernetesPod)
    CALL {
        WITH pod
        MATCH (container:KubernetesContainer)-[:WORKLOAD_PARENT]->(pod)
        RETURN container
        UNION
        WITH pod
        MATCH (pod)-[:CONTAINS]->(container:KubernetesContainer)
        RETURN container
    }
    WITH DISTINCT resource_path, cluster, pod, container
    OPTIONAL MATCH workload_parent_path=(container)-[:WORKLOAD_PARENT]->(pod)
    OPTIONAL MATCH legacy_contains_path=(pod)-[:CONTAINS]->(container)
    WITH cluster, pod, container,
         resource_path,
         coalesce(workload_parent_path, legacy_contains_path) AS controller_path
    WITH resource_path, controller_path, cluster, pod, container,
         replace(toLower(coalesce(pod.labels, '')), ' ', '') AS labels_compacted,
         toLower(coalesce(container.image, '')) AS image
    WITH resource_path, controller_path, cluster, pod, container, labels_compacted, image,
         labels_compacted CONTAINS '"app.kubernetes.io/name":"ingress-nginx"'
             AND labels_compacted CONTAINS '"app.kubernetes.io/component":"controller"'
             AS has_controller_labels,
         image CONTAINS '/ingress-nginx/controller:' AS has_controller_image
    WHERE has_controller_labels OR has_controller_image
    RETURN cluster, pod, container, resource_path, controller_path
    """,
    # Denominator is all Kubernetes clusters (the evaluated population), matching the
    # KubernetesCluster anchor so total, failing (distinct clusters running a retired
    # controller), and passing all use the same cluster unit.
    cypher_count_query="""
    MATCH (cluster:KubernetesCluster)
    RETURN COUNT(cluster) AS count
    """,
    # Aggregated per ingress-controller instance (asset_id is a synthetic composite key,
    # kept as the stable identity). Anchor on the parent KubernetesCluster node, which is
    # this fact's stated subject ("clusters running retired ingress-nginx controllers").
    asset_label="KubernetesCluster",
    asset_id_field="cluster_id",
    identity_fields=("asset_id",),
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
    MATCH (ec2:AWSEC2Instance)-[:HAS_INFORMATION]->(ssm:AWSSSMInstanceInformation)
    WHERE toLower(trim(coalesce(ssm.platform_name, ''))) = 'amazon linux'
      AND trim(toString(ssm.platform_version)) = '2'
      AND date() > date('{_AMAZON_LINUX_2_EOL_DATE}')
    OPTIONAL MATCH p=(a:AWSAccount)-[:RESOURCE]->(ec2)
    RETURN *
    """,
    cypher_count_query=f"""
    MATCH (ec2:AWSEC2Instance)-[:HAS_INFORMATION]->(ssm:AWSSSMInstanceInformation)
    WHERE toLower(trim(coalesce(ssm.platform_name, ''))) = 'amazon linux'
      AND trim(toString(ssm.platform_version)) = '2'
      AND date() > date('{_AMAZON_LINUX_2_EOL_DATE}')
    RETURN COUNT(ec2) AS count
    """,
    asset_label="AWSEC2Instance",
    asset_id_field="asset_id",
    identity_fields=("asset_id",),
    module=Module.AWS,
    maturity=Maturity.EXPERIMENTAL,
)


class EOLSoftwareOutput(Finding):
    asset_name: str | None = None
    asset_id: str | None = None
    # Populated only by the ingress-nginx fact, whose asset_id is a synthetic composite;
    # cluster_id carries the real KubernetesCluster node id it anchors on.
    cluster_id: str | None = None
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
        "as running Amazon Linux 2 after the vendor end-of-life date and "
        "deployed Kubernetes ingress-nginx controllers now that the upstream "
        "project has been retired."
    ),
    output_model=EOLSoftwareOutput,
    facts=(
        _eks_cluster_kubernetes_version_eol,
        _gke_cluster_kubernetes_version_eol,
        _aks_cluster_kubernetes_version_eol,
        _kubernetes_cluster_kubernetes_version_eol,
        _kubernetes_ingress_nginx_controller_eol,
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
    version="0.3.0",
    references=EOL_SOFTWARE_REFERENCES,
    frameworks=(iso27001_annex_a("8.8"),),
)
