from cartography.rules.spec.model import Fact
from cartography.rules.spec.model import Finding
from cartography.rules.spec.model import Framework
from cartography.rules.spec.model import Maturity
from cartography.rules.spec.model import Module
from cartography.rules.spec.model import Rule

# =============================================================================
# Shared Coverage Framework
# =============================================================================

COVERAGE_FRAMEWORK_NAME = "SubImage Coverage"
COVERAGE_FRAMEWORK_SHORT_NAME = "Coverage"
COVERAGE_FRAMEWORK_SCOPE = "subimage"

# =============================================================================
# Rule 1: SubImage Module Not Configured
# Detects SubImage modules that are not configured but have internal usage
# =============================================================================

_subimage_module_not_configured_fact = Fact(
    id="subimage-module-not-configured",
    name="SubImage Module Not Configured",
    description=(
        "Detects SubImage modules that are not configured (is_configured=false) "
        "but have a matching ThirdPartyApp in the graph, indicating internal usage "
        "of that service without coverage."
    ),
    cypher_query="""
    MATCH (m:SubImageModule)
    WHERE m.is_configured = false
    MATCH (app:ThirdPartyApp)
    WHERE toLower(app._ont_name) = toLower(m.id)
    RETURN m.name AS module_name, app.name AS app_name, app.source AS app_source
    ORDER BY m.name
    """,
    cypher_visual_query="""
    MATCH (m:SubImageModule)
    WHERE m.is_configured = false
    MATCH (app:ThirdPartyApp)
    WHERE toLower(app._ont_name) = toLower(m.id)
    RETURN *
    """,
    cypher_count_query="""
    MATCH (m:SubImageModule)
    WHERE m.is_configured = false
    MATCH (app:ThirdPartyApp)
    WHERE toLower(app._ont_name) = toLower(m.id)
    RETURN count(m) AS count
    """,
    module=Module.SUBIMAGE,
    maturity=Maturity.EXPERIMENTAL,
)


class SubImageModuleNotConfiguredOutput(Finding):
    module_name: str | None = None
    app_name: str | None = None
    app_source: str | None = None


subimage_module_not_configured = Rule(
    id="subimage_module_not_configured",
    name="SubImage Module Not Configured",
    description=(
        "Detects SubImage modules that are not configured but have matching "
        "ThirdPartyApp nodes in the graph, indicating the organization uses "
        "that service without security coverage."
    ),
    output_model=SubImageModuleNotConfiguredOutput,
    tags=(
        "subimage",
        "coverage",
        "misconfiguration",
    ),
    facts=(_subimage_module_not_configured_fact,),
    version="0.1.0",
    frameworks=(
        Framework(
            name=COVERAGE_FRAMEWORK_NAME,
            short_name=COVERAGE_FRAMEWORK_SHORT_NAME,
            requirement="1.1",
            scope=COVERAGE_FRAMEWORK_SCOPE,
        ),
    ),
)

# =============================================================================
# Rule 2: SubImage Framework Disabled While Module Enabled
# Detects frameworks that are disabled while their corresponding module is active
# =============================================================================

_subimage_framework_disabled_module_enabled_fact = Fact(
    id="subimage-framework-disabled-module-enabled",
    name="SubImage Framework Disabled While Module Enabled",
    description=(
        "Detects SubImage frameworks that are disabled while their corresponding "
        "module is configured, indicating a compliance gap."
    ),
    cypher_query="""
    MATCH (f:SubImageFramework)
    WHERE f.enabled = false
    MATCH (m:SubImageModule)
    WHERE m.is_configured = true AND f.scope = m.id
    RETURN f.name AS framework_name, f.scope AS framework_scope, m.name AS module_name
    ORDER BY f.name
    """,
    cypher_visual_query="""
    MATCH (f:SubImageFramework)
    WHERE f.enabled = false
    MATCH (m:SubImageModule)
    WHERE m.is_configured = true AND f.scope = m.id
    RETURN *
    """,
    cypher_count_query="""
    MATCH (f:SubImageFramework)
    WHERE f.enabled = false
    MATCH (m:SubImageModule)
    WHERE m.is_configured = true AND f.scope = m.id
    RETURN count(f) AS count
    """,
    module=Module.SUBIMAGE,
    maturity=Maturity.EXPERIMENTAL,
)


class SubImageFrameworkDisabledModuleEnabledOutput(Finding):
    framework_name: str | None = None
    framework_scope: str | None = None
    module_name: str | None = None


subimage_framework_disabled_module_enabled = Rule(
    id="subimage_framework_disabled_module_enabled",
    name="SubImage Framework Disabled While Module Enabled",
    description=(
        "Detects SubImage frameworks that are disabled while their corresponding "
        "module is configured and active, indicating a compliance framework gap."
    ),
    output_model=SubImageFrameworkDisabledModuleEnabledOutput,
    tags=(
        "subimage",
        "coverage",
        "compliance",
    ),
    facts=(_subimage_framework_disabled_module_enabled_fact,),
    version="0.1.0",
    frameworks=(
        Framework(
            name=COVERAGE_FRAMEWORK_NAME,
            short_name=COVERAGE_FRAMEWORK_SHORT_NAME,
            requirement="1.2",
            scope=COVERAGE_FRAMEWORK_SCOPE,
        ),
    ),
)

# =============================================================================
# Rule 3: Container Image Not Found
# Detects containers with no associated image in the graph
# =============================================================================

_container_image_not_found_fact = Fact(
    id="container-image-not-found",
    name="Container Image Not Found",
    description=(
        "Detects containers that have no HAS_IMAGE relationship, indicating "
        "the container is running an unknown or untracked image."
    ),
    cypher_query="""
    MATCH (c:Container)
    WHERE NOT (c)-[:RESOLVED_IMAGE]->(:Image)
      AND NOT coalesce(c.image, '') CONTAINS 'amazon/cloudwatch-agent'
      AND NOT coalesce(c.name, '') STARTS WITH 'aws-guardduty-agent'
    OPTIONAL MATCH (c)<-[:HAS_CONTAINER]-(cluster)
    RETURN c.name AS container_name, c.id AS container_id,
           c.image AS image, cluster.name AS cluster_name
    ORDER BY c.name
    """,
    cypher_visual_query="""
    MATCH (c:Container)
    WHERE NOT (c)-[:RESOLVED_IMAGE]->(:Image)
      AND NOT coalesce(c.image, '') CONTAINS 'amazon/cloudwatch-agent'
      AND NOT coalesce(c.name, '') STARTS WITH 'aws-guardduty-agent'
    OPTIONAL MATCH (c)<-[:HAS_CONTAINER]-(cluster)
    RETURN *
    """,
    cypher_count_query="""
    MATCH (c:Container)
    WHERE NOT (c)-[:RESOLVED_IMAGE]->(:Image)
      AND NOT coalesce(c.image, '') CONTAINS 'amazon/cloudwatch-agent'
      AND NOT coalesce(c.name, '') STARTS WITH 'aws-guardduty-agent'
    RETURN count(c) AS count
    """,
    module=Module.CROSS_CLOUD,
    maturity=Maturity.EXPERIMENTAL,
)


class ContainerImageNotFoundOutput(Finding):
    container_name: str | None = None
    container_id: str | None = None
    image: str | None = None
    cluster_name: str | None = None


container_image_not_found = Rule(
    id="container_image_not_found",
    name="Container Image Not Found",
    description=(
        "Detects containers that have no associated image in the graph. "
        "This may indicate the container is running an unknown or untracked "
        "image that cannot be scanned for vulnerabilities."
    ),
    output_model=ContainerImageNotFoundOutput,
    tags=(
        "container",
        "coverage",
        "infrastructure",
    ),
    facts=(_container_image_not_found_fact,),
    version="0.1.0",
    frameworks=(
        Framework(
            name=COVERAGE_FRAMEWORK_NAME,
            short_name=COVERAGE_FRAMEWORK_SHORT_NAME,
            requirement="2.1",
            scope=COVERAGE_FRAMEWORK_SCOPE,
        ),
    ),
)

# =============================================================================
# Rule 4: AWS Account Not Synced
# Detects AWSAccount nodes with no resources (moved from aws_account_coverage.py)
# =============================================================================

_aws_account_not_synced_fact = Fact(
    id="aws-account-not-synced",
    name="AWS Account Not Synced by Cartography",
    description=(
        "Detects AWS accounts that exist in the graph but have no resources, "
        "indicating they were discovered but not actually synced by Cartography."
    ),
    cypher_query="""
    MATCH (a:AWSAccount)
    OPTIONAL MATCH (a)-[:RESOURCE]->(n)
    WITH a, count(n) AS resource_count
    WHERE resource_count <= 1
    RETURN a.id AS account_id, a.name AS account_name, resource_count
    ORDER BY a.name
    """,
    cypher_visual_query="""
    MATCH (a:AWSAccount)
    OPTIONAL MATCH (a)-[:RESOURCE]->(n)
    WITH a, count(n) AS resource_count
    WHERE resource_count <= 1
    RETURN a
    """,
    cypher_count_query="""
    MATCH (a:AWSAccount)
    OPTIONAL MATCH (a)-[:RESOURCE]->(n)
    WITH a, count(n) AS resource_count
    WHERE resource_count <= 1
    RETURN count(a) AS count
    """,
    module=Module.AWS,
    maturity=Maturity.EXPERIMENTAL,
)


class AWSAccountNotSyncedOutput(Finding):
    account_id: str | None = None
    account_name: str | None = None
    resource_count: int | None = None


aws_account_not_synced = Rule(
    id="aws_account_not_synced",
    name="AWS Account Not Synced",
    description=(
        "Detects AWS accounts present in the graph that are not being synced "
        "by Cartography. An account with no resources indicates it was "
        "discovered (e.g. via organizations) but its resources are not being "
        "ingested."
    ),
    output_model=AWSAccountNotSyncedOutput,
    tags=(
        "aws",
        "infrastructure",
        "misconfiguration",
    ),
    facts=(_aws_account_not_synced_fact,),
    version="0.1.0",
    frameworks=(
        Framework(
            name=COVERAGE_FRAMEWORK_NAME,
            short_name=COVERAGE_FRAMEWORK_SHORT_NAME,
            requirement="2.2",
            scope=COVERAGE_FRAMEWORK_SCOPE,
        ),
    ),
)

# =============================================================================
# Rule 5: Repository Without SLSA Provenance
# Detects repos that have at least one image linked via PACKAGED_FROM with a
# match_method other than "provenance", encouraging adoption of SLSA provenance.
# =============================================================================

_repository_without_slsa_provenance_fact = Fact(
    id="repository-without-slsa-provenance",
    name="Repository Without SLSA Provenance",
    description=(
        "Detects repositories that have at least one image linked via "
        "PACKAGED_FROM with a match_method other than 'provenance', "
        "indicating images were matched by Dockerfile analysis instead of "
        "SLSA attestation."
    ),
    cypher_query="""
    MATCH (i:Image)-[r:PACKAGED_FROM]->(repo:CodeRepository)
    WHERE r.match_method <> 'provenance'
    WITH repo, collect(DISTINCT r.match_method) AS match_methods,
         count(DISTINCT i) AS image_count
    RETURN repo.id AS repo_id, repo.name AS repo_name,
           head(labels(repo)) AS repo_kind,
           image_count, match_methods
    ORDER BY repo.name
    """,
    cypher_visual_query="""
    MATCH (i:Image)-[r:PACKAGED_FROM]->(repo:CodeRepository)
    WHERE r.match_method <> 'provenance'
    RETURN *
    """,
    cypher_count_query="""
    MATCH (i:Image)-[r:PACKAGED_FROM]->(repo:CodeRepository)
    WHERE r.match_method <> 'provenance'
    RETURN count(DISTINCT repo) AS count
    """,
    module=Module.SUBIMAGE,
    maturity=Maturity.EXPERIMENTAL,
)


class RepositoryWithoutSLSAProvenanceOutput(Finding):
    repo_id: str | None = None
    repo_name: str | None = None
    repo_kind: str | None = None
    image_count: int | None = None
    match_methods: list[str] | None = None


repository_without_slsa_provenance = Rule(
    id="repository_without_slsa_provenance",
    name="Repository Without SLSA Provenance",
    description=(
        "SLSA provenance attestations are the only source-to-image link "
        "trusted enough to guarantee build traceability. Repositories "
        "still relying on Dockerfile analysis lack that guarantee and "
        "should adopt SLSA-compliant builds."
    ),
    output_model=RepositoryWithoutSLSAProvenanceOutput,
    tags=(
        "subimage",
        "coverage",
        "supply-chain",
        "slsa",
    ),
    facts=(_repository_without_slsa_provenance_fact,),
    version="0.1.0",
    frameworks=(
        Framework(
            name=COVERAGE_FRAMEWORK_NAME,
            short_name=COVERAGE_FRAMEWORK_SHORT_NAME,
            requirement="3.1",
            scope=COVERAGE_FRAMEWORK_SCOPE,
        ),
    ),
)
