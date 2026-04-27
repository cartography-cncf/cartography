"""
NIST AI RMF-Aligned Security Rules

These rules provide AI governance-focused detections aligned to NIST AI RMF 1.0
categories and are designed as practical security findings rather than
certification assertions.
"""

from cartography.rules.spec.model import Fact
from cartography.rules.spec.model import Finding
from cartography.rules.spec.model import Framework
from cartography.rules.spec.model import Maturity
from cartography.rules.spec.model import Module
from cartography.rules.spec.model import Rule
from cartography.rules.spec.model import RuleReference

NIST_REFERENCES = [
    RuleReference(
        text="NIST AI Risk Management Framework (AI RMF 1.0)",
        url="https://www.nist.gov/publications/artificial-intelligence-risk-management-framework-ai-rmf-10",
    ),
    RuleReference(
        text="NIST AI RMF Playbook",
        url="https://airc.nist.gov/airmf-resources/playbook/",
    ),
    RuleReference(
        text="NIST AI 600-1 Generative AI Profile",
        url="https://doi.org/10.6028/NIST.AI.600-1",
    ),
]

# Deterministic allowlist terms for known AI services.
AI_ALLOWLIST_TERMS = (
    "openai",
    "chatgpt",
    "anthropic",
    "claude",
    "gemini",
    "perplexity",
    "midjourney",
    "cohere",
    "huggingface",
    "hugging face",
    "notegpt",
)

# Heuristic fallback for newly observed or non-standard AI app names.
AI_HEURISTIC_REGEX = (
    ".*(openai|anthropic|gpt|claude|gemini|perplexity|midjourney|cohere|"
    "hugging ?face|genai|generative ai|llm|ai assistant).*"
)

RISKY_SCOPE_EXACT = (
    "https://mail.google.com/",
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/cloud-platform",
)

RISKY_SCOPE_PREFIXES = (
    "https://www.googleapis.com/auth/gmail",
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/calendar",
)


def _as_cypher_list(values: tuple[str, ...]) -> str:
    return "[" + ", ".join(f"'{value}'" for value in values) + "]"


AI_ALLOWLIST_TERMS_CYPHER = _as_cypher_list(AI_ALLOWLIST_TERMS)
RISKY_SCOPE_EXACT_CYPHER = _as_cypher_list(RISKY_SCOPE_EXACT)
RISKY_SCOPE_PREFIXES_CYPHER = _as_cypher_list(RISKY_SCOPE_PREFIXES)


# =============================================================================
# NIST AI RMF: AI third-party application inventory and adoption
# Main node: ThirdPartyApp
# =============================================================================
class NistAiAppInventoryOutput(Finding):
    app_name: str | None = None
    app_client_id: str | None = None
    app_source: str | None = None
    match_method: str | None = None
    authorized_identity_count: int | None = None
    authorization_event_count: int | None = None


_cross_cloud_nist_ai_app_inventory = Fact(
    id="cross_cloud_nist_ai_app_inventory",
    name="AI-related third-party app inventory",
    description=(
        "Inventories AI-related third-party applications and summarizes adoption "
        "across identities. Uses a hybrid matcher: curated allowlist plus "
        "heuristic fallback."
    ),
    cypher_query=f"""
    MATCH (app:ThirdPartyApp)
    WITH
        app,
        toLower(coalesce(app._ont_name, app.display_name, app.display_text, app.name, '')) AS normalized_name,
        toLower(coalesce(app._ont_client_id, app.client_id, app.app_id, app.id, '')) AS normalized_client_id
    WITH
        app,
        normalized_name,
        normalized_client_id,
        ANY(term IN {AI_ALLOWLIST_TERMS_CYPHER}
            WHERE normalized_name CONTAINS term OR normalized_client_id CONTAINS term
        ) AS allowlist_match,
        (normalized_name =~ '{AI_HEURISTIC_REGEX}' OR normalized_client_id =~ '{AI_HEURISTIC_REGEX}') AS heuristic_match
    WHERE allowlist_match OR heuristic_match
    OPTIONAL MATCH (ua:UserAccount)-[auth:AUTHORIZED]->(app)
    RETURN
        coalesce(app._ont_name, app.display_name, app.display_text, app.name) AS app_name,
        coalesce(app._ont_client_id, app.client_id, app.app_id, app.id) AS app_client_id,
        app._ont_source AS app_source,
        CASE
            WHEN allowlist_match THEN 'allowlist'
            WHEN heuristic_match THEN 'heuristic'
            ELSE 'unknown'
        END AS match_method,
        count(DISTINCT ua) AS authorized_identity_count,
        count(auth) AS authorization_event_count
    ORDER BY authorization_event_count DESC, app_name
    """,
    cypher_visual_query=f"""
    MATCH (app:ThirdPartyApp)
    WITH
        app,
        toLower(coalesce(app._ont_name, app.display_name, app.display_text, app.name, '')) AS normalized_name,
        toLower(coalesce(app._ont_client_id, app.client_id, app.app_id, app.id, '')) AS normalized_client_id
    WHERE
        ANY(term IN {AI_ALLOWLIST_TERMS_CYPHER}
            WHERE normalized_name CONTAINS term OR normalized_client_id CONTAINS term
        )
        OR normalized_name =~ '{AI_HEURISTIC_REGEX}'
        OR normalized_client_id =~ '{AI_HEURISTIC_REGEX}'
    OPTIONAL MATCH p=(ua:UserAccount)-[:AUTHORIZED]->(app)
    RETURN *
    """,
    cypher_count_query="""
    MATCH (app:ThirdPartyApp)
    RETURN COUNT(app) AS count
    """,
    asset_id_field="app_client_id",
    module=Module.CROSS_CLOUD,
    maturity=Maturity.EXPERIMENTAL,
)

nist_ai_third_party_app_inventory = Rule(
    id="nist_ai_third_party_app_inventory",
    name="NIST AI RMF: AI Third-Party App Inventory",
    description=(
        "Inventories AI-related third-party applications connected to enterprise "
        "identities, supporting governance and usage visibility."
    ),
    output_model=NistAiAppInventoryOutput,
    facts=(_cross_cloud_nist_ai_app_inventory,),
    tags=("ai", "identity", "compliance", "governance"),
    version="0.1.0",
    references=NIST_REFERENCES,
    frameworks=(
        Framework(
            name="NIST AI Risk Management Framework",
            short_name="NIST-AI-RMF",
            requirement="MAP 1",
            revision="1.0",
        ),
    ),
)


# =============================================================================
# NIST AI RMF: AI third-party apps with sensitive OAuth scopes
# Main node: ThirdPartyApp
# =============================================================================
class NistAiSensitiveScopesOutput(Finding):
    app_name: str | None = None
    app_client_id: str | None = None
    app_source: str | None = None
    authorized_identity_count: int | None = None
    risky_scope_count: int | None = None
    risky_scopes: list[str] | None = None


_cross_cloud_nist_ai_app_sensitive_scopes = Fact(
    id="cross_cloud_nist_ai_app_sensitive_scopes",
    name="AI-related third-party apps with sensitive OAuth scopes",
    description=(
        "Finds AI-related third-party apps with broad or high-risk OAuth scopes "
        "(for example Google Drive, Gmail, Calendar, and cloud-platform scopes)."
    ),
    cypher_query=f"""
    MATCH (ua:UserAccount)-[auth:AUTHORIZED]->(app:ThirdPartyApp)
    WITH
        ua,
        auth,
        app,
        toLower(coalesce(app._ont_name, app.display_name, app.display_text, app.name, '')) AS normalized_name,
        toLower(coalesce(app._ont_client_id, app.client_id, app.app_id, app.id, '')) AS normalized_client_id
    WHERE
        ANY(term IN {AI_ALLOWLIST_TERMS_CYPHER}
            WHERE normalized_name CONTAINS term OR normalized_client_id CONTAINS term
        )
        OR normalized_name =~ '{AI_HEURISTIC_REGEX}'
        OR normalized_client_id =~ '{AI_HEURISTIC_REGEX}'
    WITH
        ua,
        app,
        [scope IN coalesce(auth.scopes, [])
            WHERE scope IN {RISKY_SCOPE_EXACT_CYPHER}
                OR ANY(prefix IN {RISKY_SCOPE_PREFIXES_CYPHER} WHERE scope STARTS WITH prefix)
        ] AS risky_scopes_for_auth
    WHERE size(risky_scopes_for_auth) > 0
    UNWIND risky_scopes_for_auth AS risky_scope
    RETURN
        coalesce(app._ont_name, app.display_name, app.display_text, app.name) AS app_name,
        coalesce(app._ont_client_id, app.client_id, app.app_id, app.id) AS app_client_id,
        app._ont_source AS app_source,
        count(DISTINCT ua) AS authorized_identity_count,
        count(DISTINCT risky_scope) AS risky_scope_count,
        collect(DISTINCT risky_scope) AS risky_scopes
    ORDER BY risky_scope_count DESC, authorized_identity_count DESC, app_name
    """,
    cypher_visual_query=f"""
    MATCH p=(ua:UserAccount)-[auth:AUTHORIZED]->(app:ThirdPartyApp)
    WITH
        p,
        auth,
        app,
        toLower(coalesce(app._ont_name, app.display_name, app.display_text, app.name, '')) AS normalized_name,
        toLower(coalesce(app._ont_client_id, app.client_id, app.app_id, app.id, '')) AS normalized_client_id
    WHERE
        (
            ANY(term IN {AI_ALLOWLIST_TERMS_CYPHER}
                WHERE normalized_name CONTAINS term OR normalized_client_id CONTAINS term
            )
            OR normalized_name =~ '{AI_HEURISTIC_REGEX}'
            OR normalized_client_id =~ '{AI_HEURISTIC_REGEX}'
        )
        AND ANY(scope IN coalesce(auth.scopes, [])
            WHERE scope IN {RISKY_SCOPE_EXACT_CYPHER}
                OR ANY(prefix IN {RISKY_SCOPE_PREFIXES_CYPHER} WHERE scope STARTS WITH prefix)
        )
    RETURN *
    """,
    cypher_count_query="""
    MATCH (app:ThirdPartyApp)
    RETURN COUNT(app) AS count
    """,
    asset_id_field="app_client_id",
    module=Module.CROSS_CLOUD,
    maturity=Maturity.EXPERIMENTAL,
)

nist_ai_third_party_app_sensitive_scopes = Rule(
    id="nist_ai_third_party_app_sensitive_scopes",
    name="NIST AI RMF: AI Third-Party Apps with Sensitive Scopes",
    description=(
        "Detects AI-related third-party applications that hold sensitive OAuth "
        "grants and therefore increase data exposure risk."
    ),
    output_model=NistAiSensitiveScopesOutput,
    facts=(_cross_cloud_nist_ai_app_sensitive_scopes,),
    tags=("ai", "identity", "oauth", "compliance"),
    version="0.1.0",
    references=NIST_REFERENCES,
    frameworks=(
        Framework(
            name="NIST AI Risk Management Framework",
            short_name="NIST-AI-RMF",
            requirement="MEASURE 2",
            revision="1.0",
        ),
        Framework(
            name="NIST AI Risk Management Framework",
            short_name="NIST-AI-RMF",
            requirement="MANAGE 2",
            revision="1.0",
        ),
    ),
)


# =============================================================================
# NIST AI RMF: Privileged identities authorizing AI apps
# Main node: ThirdPartyApp
# =============================================================================
class NistAiAdminAuthorizationsOutput(Finding):
    app_name: str | None = None
    app_client_id: str | None = None
    app_source: str | None = None
    admin_user_count: int | None = None
    authorization_event_count: int | None = None


_gw_nist_ai_admin_app_authorizations = Fact(
    id="gw_nist_ai_admin_app_authorizations",
    name="Google Workspace admins authorizing AI-related apps",
    description=(
        "Finds Google Workspace administrator accounts that have authorized "
        "AI-related third-party apps."
    ),
    cypher_query=f"""
    MATCH (u:GoogleWorkspaceUser)-[auth:AUTHORIZED]->(app:ThirdPartyApp)
    WITH
        u,
        auth,
        app,
        toLower(coalesce(app._ont_name, app.display_name, app.display_text, app.name, '')) AS normalized_name,
        toLower(coalesce(app._ont_client_id, app.client_id, app.app_id, app.id, '')) AS normalized_client_id
    WHERE u.is_admin = true
      AND (
            ANY(term IN {AI_ALLOWLIST_TERMS_CYPHER}
                WHERE normalized_name CONTAINS term OR normalized_client_id CONTAINS term
            )
            OR normalized_name =~ '{AI_HEURISTIC_REGEX}'
            OR normalized_client_id =~ '{AI_HEURISTIC_REGEX}'
      )
    RETURN
        coalesce(app._ont_name, app.display_name, app.display_text, app.name) AS app_name,
        coalesce(app._ont_client_id, app.client_id, app.app_id, app.id) AS app_client_id,
        app._ont_source AS app_source,
        count(DISTINCT u) AS admin_user_count,
        count(auth) AS authorization_event_count
    ORDER BY admin_user_count DESC, authorization_event_count DESC, app_name
    """,
    cypher_visual_query=f"""
    MATCH p=(u:GoogleWorkspaceUser)-[:AUTHORIZED]->(app:ThirdPartyApp)
    WITH
        p,
        u,
        app,
        toLower(coalesce(app._ont_name, app.display_name, app.display_text, app.name, '')) AS normalized_name,
        toLower(coalesce(app._ont_client_id, app.client_id, app.app_id, app.id, '')) AS normalized_client_id
    WHERE u.is_admin = true
      AND (
            ANY(term IN {AI_ALLOWLIST_TERMS_CYPHER}
                WHERE normalized_name CONTAINS term OR normalized_client_id CONTAINS term
            )
            OR normalized_name =~ '{AI_HEURISTIC_REGEX}'
            OR normalized_client_id =~ '{AI_HEURISTIC_REGEX}'
      )
    RETURN *
    """,
    cypher_count_query=f"""
    MATCH (u:GoogleWorkspaceUser)-[:AUTHORIZED]->(app:ThirdPartyApp)
    WITH
        u,
        app,
        toLower(coalesce(app._ont_name, app.display_name, app.display_text, app.name, '')) AS normalized_name,
        toLower(coalesce(app._ont_client_id, app.client_id, app.app_id, app.id, '')) AS normalized_client_id
    WHERE
        u.is_admin = true
        AND (
            ANY(term IN {AI_ALLOWLIST_TERMS_CYPHER}
                WHERE normalized_name CONTAINS term OR normalized_client_id CONTAINS term
            )
            OR normalized_name =~ '{AI_HEURISTIC_REGEX}'
            OR normalized_client_id =~ '{AI_HEURISTIC_REGEX}'
        )
    RETURN COUNT(DISTINCT app) AS count
    """,
    asset_id_field="app_client_id",
    module=Module.GOOGLEWORKSPACE,
    maturity=Maturity.EXPERIMENTAL,
)

nist_ai_admin_ai_app_authorizations = Rule(
    id="nist_ai_admin_ai_app_authorizations",
    name="NIST AI RMF: Admin Authorization of AI Apps",
    description=(
        "Identifies privileged Google Workspace identities that have authorized "
        "AI-related third-party applications."
    ),
    output_model=NistAiAdminAuthorizationsOutput,
    facts=(_gw_nist_ai_admin_app_authorizations,),
    tags=("ai", "identity", "privileged_access", "compliance"),
    version="0.1.0",
    references=NIST_REFERENCES,
    frameworks=(
        Framework(
            name="NIST AI Risk Management Framework",
            short_name="NIST-AI-RMF",
            requirement="GOVERN 5",
            revision="1.0",
        ),
    ),
)


# =============================================================================
# NIST AI RMF: Deployed AI agent inventory from AIBOM
# Main node: AIBOMComponent (AIAgent)
# =============================================================================
class NistAiAibomAgentInventoryOutput(Finding):
    source_id: str | None = None
    image_uri: str | None = None
    manifest_digest: str | None = None
    scanner_name: str | None = None
    scanner_version: str | None = None
    agent_component_id: str | None = None
    agent_logical_id: str | None = None
    agent_name: str | None = None
    agent_framework: str | None = None
    agent_file_path: str | None = None
    agent_line_number: int | None = None
    model_count: int | None = None
    model_names: list[str] | None = None
    tool_count: int | None = None
    tool_names: list[str] | None = None
    memory_count: int | None = None
    memory_names: list[str] | None = None
    prompt_count: int | None = None
    prompt_names: list[str] | None = None
    embedding_count: int | None = None
    embedding_names: list[str] | None = None


_aibom_nist_ai_agent_inventory = Fact(
    id="aibom_nist_ai_agent_inventory",
    name="Deployed AI agent inventory from AIBOM",
    description=(
        "Inventories deployed AI agents discovered by AIBOM and summarizes the "
        "models, tools, memory stores, prompts, and embeddings each agent uses."
    ),
    cypher_query="""
    MATCH (source:AIBOMSource)-[:SCANNED_IMAGE]->(img:Image)
    MATCH (source)-[:HAS_COMPONENT]->(agent:AIAgent)
    WITH DISTINCT source, img, agent
    OPTIONAL MATCH (agent)-[:USES_MODEL]->(model:AIModel)
    WITH source, img, agent, collect(DISTINCT model.name) AS model_names
    OPTIONAL MATCH (agent)-[:USES_TOOL]->(tool:AITool)
    WITH source, img, agent, model_names, collect(DISTINCT tool.name) AS tool_names
    OPTIONAL MATCH (agent)-[:USES_MEMORY]->(memory:AIMemory)
    WITH
        source,
        img,
        agent,
        model_names,
        tool_names,
        collect(DISTINCT memory.name) AS memory_names
    OPTIONAL MATCH (agent)-[:USES_PROMPT]->(prompt:AIPrompt)
    WITH
        source,
        img,
        agent,
        model_names,
        tool_names,
        memory_names,
        collect(DISTINCT prompt.name) AS prompt_names
    OPTIONAL MATCH (agent)-[:USES_EMBEDDING]->(embedding:AIEmbedding)
    WITH
        source,
        img,
        agent,
        model_names,
        tool_names,
        memory_names,
        prompt_names,
        count(DISTINCT embedding) AS embedding_count,
        collect(DISTINCT embedding.name) AS embedding_names
    RETURN
        source.id AS source_id,
        source.image_uri AS image_uri,
        img._ont_digest AS manifest_digest,
        source.scanner_name AS scanner_name,
        source.scanner_version AS scanner_version,
        agent.id AS agent_component_id,
        agent.logical_id AS agent_logical_id,
        agent.name AS agent_name,
        agent.framework AS agent_framework,
        agent.file_path AS agent_file_path,
        agent.line_number AS agent_line_number,
        size(model_names) AS model_count,
        model_names,
        size(tool_names) AS tool_count,
        tool_names,
        size(memory_names) AS memory_count,
        memory_names,
        size(prompt_names) AS prompt_count,
        prompt_names,
        embedding_count,
        embedding_names
    ORDER BY image_uri, agent_name
    """,
    cypher_visual_query="""
    MATCH p=(source:AIBOMSource)-[:SCANNED_IMAGE]->(img:Image)
    MATCH p1=(source)-[:HAS_COMPONENT]->(agent:AIAgent)
    OPTIONAL MATCH p2=(agent)-[:USES_MODEL]->(:AIModel)
    OPTIONAL MATCH p3=(agent)-[:USES_TOOL]->(:AITool)
    OPTIONAL MATCH p4=(agent)-[:USES_MEMORY]->(:AIMemory)
    OPTIONAL MATCH p5=(agent)-[:USES_PROMPT]->(:AIPrompt)
    OPTIONAL MATCH p6=(agent)-[:USES_EMBEDDING]->(:AIEmbedding)
    RETURN *
    """,
    cypher_count_query="""
    MATCH (source:AIBOMSource)-[:SCANNED_IMAGE]->(:Image)
    MATCH (source)-[:HAS_COMPONENT]->(agent:AIAgent)
    RETURN COUNT(DISTINCT agent) AS count
    """,
    asset_id_field="agent_component_id",
    module=Module.AIBOM,
    maturity=Maturity.EXPERIMENTAL,
)

nist_ai_aibom_agent_inventory = Rule(
    id="nist_ai_aibom_agent_inventory",
    name="NIST AI RMF: Deployed AI Agent Inventory",
    description=(
        "Inventories deployed AI agents from AIBOM and their direct agentic "
        "dependencies so teams can map runtime AI system composition."
    ),
    output_model=NistAiAibomAgentInventoryOutput,
    facts=(_aibom_nist_ai_agent_inventory,),
    tags=("ai", "inventory", "software_supply_chain", "compliance"),
    version="0.1.0",
    references=NIST_REFERENCES,
    frameworks=(
        Framework(
            name="NIST AI Risk Management Framework",
            short_name="NIST-AI-RMF",
            requirement="MAP 1",
            revision="1.0",
        ),
        Framework(
            name="NIST AI Risk Management Framework",
            short_name="NIST-AI-RMF",
            requirement="GOVERN 1",
            revision="1.0",
        ),
    ),
)


# =============================================================================
# NIST AI RMF: AIBOM coverage and provenance gaps
# Main node: AIBOMSource
# =============================================================================
class NistAiAibomCoverageGapOutput(Finding):
    source_id: str | None = None
    image_uri: str | None = None
    manifest_digests: list[str] | None = None
    report_location: str | None = None
    scanner_name: str | None = None
    scanner_version: str | None = None
    source_status: str | None = None
    analysis_status: str | None = None
    image_matched: bool | None = None
    total_components: int | None = None
    gap_reason: str | None = None


_aibom_nist_ai_coverage_gaps = Fact(
    id="aibom_nist_ai_coverage_gaps",
    name="AIBOM coverage and provenance gaps",
    description=(
        "Finds AIBOM sources that did not complete successfully or failed to map "
        "to a canonical image, indicating gaps in deployed AI inventory."
    ),
    cypher_query="""
    MATCH (source:AIBOMSource)
    WITH
        source,
        CASE
            WHEN coalesce(source.image_matched, false) = false THEN 'unmatched_image'
            WHEN toLower(coalesce(source.source_status, 'completed')) <> 'completed' THEN 'incomplete_source'
            WHEN source.analysis_status IS NOT NULL
                 AND toLower(source.analysis_status) <> 'completed' THEN 'analysis_not_completed'
            ELSE NULL
        END AS gap_reason
    WHERE gap_reason IS NOT NULL
    RETURN
        source.id AS source_id,
        source.image_uri AS image_uri,
        source.manifest_digests AS manifest_digests,
        source.report_location AS report_location,
        source.scanner_name AS scanner_name,
        source.scanner_version AS scanner_version,
        source.source_status AS source_status,
        source.analysis_status AS analysis_status,
        source.image_matched AS image_matched,
        source.total_components AS total_components,
        gap_reason
    ORDER BY gap_reason, image_uri
    """,
    cypher_visual_query="""
    MATCH (source:AIBOMSource)
    WHERE
        coalesce(source.image_matched, false) = false
        OR toLower(coalesce(source.source_status, 'completed')) <> 'completed'
        OR (
            source.analysis_status IS NOT NULL
            AND toLower(source.analysis_status) <> 'completed'
        )
    OPTIONAL MATCH p=(source)-[:SCANNED_IMAGE]->(:Image)
    RETURN source, p
    """,
    cypher_count_query="""
    MATCH (source:AIBOMSource)
    RETURN COUNT(source) AS count
    """,
    asset_id_field="source_id",
    module=Module.AIBOM,
    maturity=Maturity.EXPERIMENTAL,
)

nist_ai_aibom_coverage_gaps = Rule(
    id="nist_ai_aibom_coverage_gaps",
    name="NIST AI RMF: AIBOM Coverage Gaps",
    description=(
        "Detects deployed AI inventory gaps where AIBOM scans are incomplete or "
        "cannot be tied back to the canonical production image."
    ),
    output_model=NistAiAibomCoverageGapOutput,
    facts=(_aibom_nist_ai_coverage_gaps,),
    tags=("ai", "inventory", "provenance", "compliance"),
    version="0.1.0",
    references=NIST_REFERENCES,
    frameworks=(
        Framework(
            name="NIST AI Risk Management Framework",
            short_name="NIST-AI-RMF",
            requirement="MEASURE 2",
            revision="1.0",
        ),
        Framework(
            name="NIST AI Risk Management Framework",
            short_name="NIST-AI-RMF",
            requirement="MANAGE 2",
            revision="1.0",
        ),
    ),
)


# =============================================================================
# NIST AI RMF: AI provider API key hygiene
# Main node: OpenAIApiKey/OpenAIAdminApiKey/AnthropicApiKey
# =============================================================================
class NistAiProviderApiKeyHygieneOutput(Finding):
    provider: str | None = None
    organization_id: str | None = None
    project_or_workspace_id: str | None = None
    api_key_id: str | None = None
    api_key_name: str | None = None
    status: str | None = None
    created_at: str | None = None
    last_used_at: str | None = None
    is_stale_or_unused: bool | None = None
    has_owner: bool | None = None
    has_project_or_workspace_scope: bool | None = None


_openai_nist_ai_stale_or_unowned_api_keys = Fact(
    id="openai_nist_ai_stale_or_unowned_api_keys",
    name="OpenAI API keys stale/unused or lacking owner attribution",
    description=(
        "Finds OpenAI API keys that are stale/unused (90+ days) or lack clear "
        "owner attribution."
    ),
    cypher_query="""
    MATCH (k)
    WHERE k:OpenAIApiKey OR k:OpenAIAdminApiKey
    OPTIONAL MATCH (project:OpenAIProject)-[:RESOURCE]->(k)
    OPTIONAL MATCH (org_from_project:OpenAIOrganization)-[:RESOURCE]->(project)
    OPTIONAL MATCH (org_direct:OpenAIOrganization)-[:RESOURCE]->(k)
    WITH k, project, coalesce(org_from_project, org_direct) AS org
    OPTIONAL MATCH (u:OpenAIUser)-[:OWNS]->(k)
    WITH org, k, project, count(u) > 0 AS has_user_owner
    OPTIONAL MATCH (sa:OpenAIServiceAccount)-[:OWNS]->(k)
    WITH org, k, project, has_user_owner, count(sa) > 0 AS has_sa_owner
    WITH org, k, project, has_user_owner OR has_sa_owner AS has_owner
    WITH
        org,
        k,
        project,
        has_owner,
        CASE
            WHEN k.last_used_at IS NULL THEN true
            ELSE datetime({epochSeconds: toInteger(k.last_used_at)}) < datetime() - duration('P90D')
        END AS is_stale_or_unused
    WHERE is_stale_or_unused OR NOT has_owner
    RETURN
        'openai' AS provider,
        org.id AS organization_id,
        project.id AS project_or_workspace_id,
        k.id AS api_key_id,
        k.name AS api_key_name,
        CASE
            WHEN k:OpenAIAdminApiKey THEN 'active'
            ELSE coalesce(project.status, 'active')
        END AS status,
        toString(k.created_at) AS created_at,
        toString(k.last_used_at) AS last_used_at,
        is_stale_or_unused,
        has_owner,
        project IS NOT NULL AS has_project_or_workspace_scope
    ORDER BY provider, organization_id, api_key_name
    """,
    cypher_visual_query="""
    MATCH (k)
    WHERE k:OpenAIApiKey OR k:OpenAIAdminApiKey
    OPTIONAL MATCH p=(org_direct:OpenAIOrganization)-[:RESOURCE]->(k)
    OPTIONAL MATCH p3=(project:OpenAIProject)-[:RESOURCE]->(k)
    OPTIONAL MATCH p4=(org_from_project:OpenAIOrganization)-[:RESOURCE]->(project)
    OPTIONAL MATCH p1=(u:OpenAIUser)-[:OWNS]->(k)
    OPTIONAL MATCH p2=(sa:OpenAIServiceAccount)-[:OWNS]->(k)
    WITH p, p1, p2, p3, p4, k
    WITH
        p, p1, p2, p3, p4,
        CASE
            WHEN k.last_used_at IS NULL THEN true
            ELSE datetime({epochSeconds: toInteger(k.last_used_at)}) < datetime() - duration('P90D')
        END AS is_stale_or_unused,
        (p1 IS NOT NULL OR p2 IS NOT NULL) AS has_owner
    WHERE is_stale_or_unused OR NOT has_owner
    RETURN *
    """,
    cypher_count_query="""
    MATCH (k)
    WHERE k:OpenAIApiKey OR k:OpenAIAdminApiKey
    RETURN COUNT(k) AS count
    """,
    asset_id_field="api_key_id",
    module=Module.OPENAI,
    maturity=Maturity.EXPERIMENTAL,
)


_anthropic_nist_ai_stale_or_unscoped_api_keys = Fact(
    id="anthropic_nist_ai_stale_or_unscoped_api_keys",
    name="Anthropic API keys stale/unused or lacking ownership/scope",
    description=(
        "Finds Anthropic API keys that are stale/unused (90+ days), lack owner "
        "attribution, or are not scoped to a workspace."
    ),
    cypher_query="""
    MATCH (org:AnthropicOrganization)-[:RESOURCE]->(k:AnthropicApiKey)
    OPTIONAL MATCH (u:AnthropicUser)-[:OWNS]->(k)
    WITH org, k, count(u) > 0 AS has_owner
    OPTIONAL MATCH (workspace:AnthropicWorkspace)-[:CONTAINS]->(k)
    WITH
        org,
        k,
        has_owner,
        workspace,
        CASE
            WHEN k.last_used_at IS NULL THEN true
            ELSE datetime(k.last_used_at) < datetime() - duration('P90D')
        END AS is_stale_or_unused
    WITH
        org,
        k,
        has_owner,
        workspace,
        is_stale_or_unused,
        workspace IS NOT NULL AS has_project_or_workspace_scope
    WHERE is_stale_or_unused OR NOT has_owner OR NOT has_project_or_workspace_scope
    RETURN
        'anthropic' AS provider,
        org.id AS organization_id,
        workspace.id AS project_or_workspace_id,
        k.id AS api_key_id,
        k.name AS api_key_name,
        coalesce(k.status, 'unknown') AS status,
        toString(k.created_at) AS created_at,
        toString(k.last_used_at) AS last_used_at,
        is_stale_or_unused,
        has_owner,
        has_project_or_workspace_scope
    ORDER BY provider, organization_id, api_key_name
    """,
    cypher_visual_query="""
    MATCH p=(org:AnthropicOrganization)-[:RESOURCE]->(k:AnthropicApiKey)
    OPTIONAL MATCH p1=(u:AnthropicUser)-[:OWNS]->(k)
    OPTIONAL MATCH p2=(workspace:AnthropicWorkspace)-[:CONTAINS]->(k)
    WITH p, p1, p2, k
    WITH
        p, p1, p2,
        CASE
            WHEN k.last_used_at IS NULL THEN true
            ELSE datetime(k.last_used_at) < datetime() - duration('P90D')
        END AS is_stale_or_unused,
        p1 IS NOT NULL AS has_owner,
        p2 IS NOT NULL AS has_project_or_workspace_scope
    WHERE is_stale_or_unused OR NOT has_owner OR NOT has_project_or_workspace_scope
    RETURN *
    """,
    cypher_count_query="""
    MATCH (k:AnthropicApiKey)
    RETURN COUNT(k) AS count
    """,
    asset_id_field="api_key_id",
    module=Module.ANTHROPIC,
    maturity=Maturity.EXPERIMENTAL,
)

nist_ai_provider_api_key_hygiene = Rule(
    id="nist_ai_provider_api_key_hygiene",
    name="NIST AI RMF: AI Provider API Key Hygiene",
    description=(
        "Detects stale/unused AI-provider API keys and ownership/scope gaps across "
        "OpenAI and Anthropic."
    ),
    output_model=NistAiProviderApiKeyHygieneOutput,
    facts=(
        _openai_nist_ai_stale_or_unowned_api_keys,
        _anthropic_nist_ai_stale_or_unscoped_api_keys,
    ),
    tags=("ai", "credentials", "governance", "compliance"),
    version="0.1.0",
    references=NIST_REFERENCES,
    frameworks=(
        Framework(
            name="NIST AI Risk Management Framework",
            short_name="NIST-AI-RMF",
            requirement="GOVERN 5",
            revision="1.0",
        ),
        Framework(
            name="NIST AI Risk Management Framework",
            short_name="NIST-AI-RMF",
            requirement="MANAGE 2",
            revision="1.0",
        ),
    ),
)
