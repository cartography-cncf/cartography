from pathlib import Path

import cartography.models.aibom as aibom_models
import cartography.models.airbyte as airbyte_models
import cartography.models.anthropic as anthropic_models
import cartography.models.bigfix as bigfix_models
import cartography.models.circleci as circleci_models
import cartography.models.cloudflare as cloudflare_models
import cartography.models.crowdstrike as crowdstrike_models
import cartography.models.cve as cve_models
import cartography.models.cve_metadata as cve_metadata_models
import cartography.models.digitalocean as digitalocean_models
import cartography.models.docker_scout as docker_scout_models
import cartography.models.duo as duo_models
import cartography.models.googleworkspace as googleworkspace_models
import cartography.models.gsuite as gsuite_models
import cartography.models.jumpcloud as jumpcloud_models
import cartography.models.kandji as kandji_models
import cartography.models.keycloak as keycloak_models
import cartography.models.lastpass as lastpass_models
import cartography.models.oci as oci_models
import cartography.models.openai as openai_models
import cartography.models.pagerduty as pagerduty_models
import cartography.models.salesforce as salesforce_models
import cartography.models.sentry as sentry_models
import cartography.models.slack as slack_models
import cartography.models.snipeit as snipeit_models
import cartography.models.spacelift as spacelift_models
import cartography.models.subimage as subimage_models
import cartography.models.syft as syft_models
import cartography.models.tailscale as tailscale_models
import cartography.models.vercel as vercel_models
import cartography.models.workday as workday_models
import cartography.models.workos as workos_models
from cartography.models.core.relationships import LinkDirection
from cartography.models.introspection import DataModel
from cartography.models.introspection import inspect_data_model
from cartography.models.introspection import Node
from cartography.models.introspection import PermissionRelationshipDefinition
from cartography.models.introspection import Relationship
from cartography.models.schema_docs import GENERATED_NOTICE
from cartography.models.schema_docs import render_module_schema
from cartography.models.schema_docs import write_module_schema_docs


def test_aibom_schema_doc_is_generated_from_introspected_model():
    # Arrange
    model = inspect_data_model(aibom_models)

    # Act
    generated = render_module_schema(model, "aibom")

    # Assert
    assert not Path("docs/root/modules/aibom/schema.md").exists()
    assert len(model.nodes) == 2
    assert len(model.relationships) == 12
    assert "## AIBOM Schema" in generated
    assert "`AIAgent` when `category` equals `agent`." in generated
    assert "`AIModel` (ontology label) when `category` equals `model`." in generated
    assert (
        "| *_ont_source* |  | Module that populated this node's ontology fields. |"
        in generated
    )
    assert "(:AIBOMSource)-[:RUNS_ON]->(:Container)" in generated
    assert "No description provided." not in generated


def test_airbyte_schema_doc_is_generated_from_introspected_model():
    # Arrange
    model = inspect_data_model(airbyte_models)

    # Act
    generated = render_module_schema(model, "airbyte")

    # Assert
    assert not Path("docs/root/modules/airbyte/schema.md").exists()
    assert len(model.nodes) == 8
    assert len(model.relationships) == 18
    assert "An Airbyte connection that synchronizes source data" in generated
    assert "| config_host |  | Configured source host. |" in generated
    assert "(:AirbyteConnection)-[:SYNC_FROM]->(:AirbyteSource)" in generated
    assert "No description provided." not in generated


def test_circleci_schema_doc_is_generated_from_introspected_model():
    # Arrange
    model = inspect_data_model(circleci_models)

    # Act
    generated = render_module_schema(model, "circleci")

    # Assert
    assert not Path("docs/root/modules/circleci/schema.md").exists()
    assert len(model.nodes) == 15
    assert len(model.relationships) == 21
    assert (
        "| vcs_login |  | GitHub organization login derived from the CircleCI slug. |"
        in generated
    )
    assert (
        "(:CircleCIOrganization)-[:ASSOCIATED_WITH]->(:GitHubOrganization)" in generated
    )
    assert "No description provided." not in generated


def test_cve_metadata_schema_doc_is_generated_from_introspected_model():
    # Arrange
    model = inspect_data_model(cve_metadata_models)

    # Act
    generated = render_module_schema(model, "cve_metadata")

    # Assert
    assert not Path("docs/root/modules/cve_metadata/schema.md").exists()
    assert len(model.nodes) == 2
    assert len(model.relationships) == 2
    assert (
        "| effect_tags |  | Controlled technical effects derived from mapped CWEs when "
        "available, otherwise from high CVSS confidentiality, integrity, and "
        "availability impacts plus the network straight-shot rule. Values are "
        "execute-code, gain-privileges, access-credentials, bypass-control, "
        "disclose-data, tamper-data, and deny-service. |"
    ) in generated
    assert "(:CVEMetadata)-[:ENRICHES]->(:CVE)" in generated
    assert "No description provided." not in generated


def test_cve_schema_doc_is_generated_from_introspected_model():
    # Arrange
    model = inspect_data_model(cve_models)

    # Act
    generated = render_module_schema(model, "cve")

    # Assert
    assert not Path("docs/root/modules/cve/schema.md").exists()
    assert len(model.nodes) == 2
    assert len(model.relationships) == 2
    assert (
        "| cve_id | Yes | CVE identifier indexed for cross-module correlation. |"
        in generated
    )
    assert "(:SpotlightVulnerability)-[:HAS_CVE]->(:CVE)" in generated
    assert "No description provided." not in generated


def test_syft_schema_doc_is_generated_from_introspected_model():
    # Arrange
    model = inspect_data_model(syft_models)

    # Act
    generated = render_module_schema(model, "syft")

    # Assert
    assert not Path("docs/root/modules/syft/schema.md").exists()
    assert len(model.nodes) == 1
    assert len(model.relationships) == 2
    assert "(:SyftPackage)-[:DEPENDS_ON]->(:SyftPackage)" in generated
    assert "No description provided." not in generated


def test_crowdstrike_schema_doc_is_generated_from_introspected_model():
    # Arrange
    model = inspect_data_model(crowdstrike_models)

    # Act
    generated = render_module_schema(model, "crowdstrike")

    # Assert
    assert not Path("docs/root/modules/crowdstrike/schema.md").exists()
    assert len(model.nodes) == 4
    assert len(model.relationships) == 4
    assert (
        "(:CrowdstrikeHost)-[:HAS_VULNERABILITY]->(:SpotlightVulnerability)"
        in generated
    )
    assert "No description provided." not in generated


def test_tailscale_schema_doc_is_generated_from_introspected_model():
    # Arrange
    model = inspect_data_model(tailscale_models)
    complete_model = inspect_data_model()

    # Act
    generated = render_module_schema(complete_model, "tailscale")

    # Assert
    assert not Path("docs/root/modules/tailscale/schema.md").exists()
    assert len(model.nodes) == 10
    assert len(model.relationships) == 30
    assert "(:TailscaleUser)-[:CAN_ACCESS]->(:TailscaleDevice)" in generated
    assert "(:TailscaleDevice)-[:IS_INSTANCE]->(:ComputeInstance)" in generated
    assert "No description provided." not in generated


def test_lastpass_schema_doc_is_generated_from_introspected_model():
    # Arrange
    model = inspect_data_model(lastpass_models)

    # Act
    generated = render_module_schema(model, "lastpass")

    # Assert
    assert not Path("docs/root/modules/lastpass/schema.md").exists()
    assert generated.startswith(GENERATED_NOTICE)
    assert "| email | Yes | Email address of the user. |" in generated
    assert "(:Human)-[:IDENTITY_LASTPASS]->(:LastpassUser)" in generated
    assert (
        "> **Ontology Mapping**: This node uses the ontology label `UserAccount`."
        in generated
    )
    assert (
        "| *_ont_email* | Yes | Normalized field sourced from `email`. |" in generated
    )
    assert generated.index("| multifactor |") < generated.index("| *_ont_email* |")
    assert "| Field | Index | Description |" in generated


def test_typed_analysis_jobs_are_rendered_from_introspected_model():
    # Arrange
    model = inspect_data_model(gsuite_models)

    # Act
    generated = render_module_schema(model, "gsuite")

    # Assert
    assert (
        "Analysis job `GSuite user map to Human` generates "
        "`(:Human)-[:IDENTITY_GSUITE]->(:GSuiteUser)`."
    ) in generated


def test_gsuite_schema_doc_is_generated_from_introspected_model():
    # Arrange
    model = inspect_data_model(gsuite_models)

    # Act
    generated = render_module_schema(model, "gsuite")

    # Assert
    assert not Path("docs/root/modules/gsuite/schema.md").exists()
    assert len(model.nodes) == 3
    assert len(model.relationships) == 9
    assert "| email | Yes | Primary email address of the user. |" in generated
    assert (
        "Deprecated compatibility edge linking a member group to its parent group."
        in generated
    )
    assert "No description provided." not in generated


def test_googleworkspace_schema_doc_is_generated_from_introspected_model():
    # Arrange
    model = inspect_data_model(googleworkspace_models)

    # Act
    generated = render_module_schema(model, "googleworkspace")

    # Assert
    assert not Path("docs/root/modules/googleworkspace/schema.md").exists()
    assert len(model.nodes) == 5
    assert len(model.relationships) == 14
    assert "| display_name |  | Display name of the group. |" in generated
    assert "(:GoogleWorkspaceGroup)-[:MEMBER_OF]->(:GoogleWorkspaceGroup)" in generated
    assert (
        "(:GoogleWorkspaceUser)-[:INHERITED_MEMBER_OF]->"
        "(:GoogleWorkspaceGroup)" in generated
    )
    assert "No description provided." not in generated


def test_jamf_schema_doc_is_generated_from_introspected_model():
    # Arrange
    model = inspect_data_model()

    # Act
    generated = render_module_schema(model, "jamf")

    # Assert
    assert not Path("docs/root/modules/jamf/schema.md").exists()
    assert len(tuple(node for node in model.nodes if "jamf" in node.modules)) == 5
    assert (
        "**Ontology Projection**: `JamfComputer` contributes data to canonical "
        "`Device` nodes." in generated
    )
    assert (
        "**Ontology Projection**: `JamfMobileDevice` contributes data to canonical "
        "`Device` nodes." in generated
    )
    assert "**Additional Labels**: This node also uses `Tenant`." in generated
    assert "(:Device)-[:OBSERVED_AS]->(:JamfComputer)" in generated
    assert "(:User)-[:OWNS]->(:Device)" not in generated
    assert "_ont_hostname" not in generated
    assert "_ont_source" not in generated
    computer_group_section = generated.split("### JamfComputerGroup", 1)[1].split(
        "### ",
        1,
    )[0]
    assert "No relationships." not in computer_group_section
    assert "No description provided." not in generated


def test_undirected_analysis_relationships_are_rendered_without_arrows():
    # Arrange
    node = Node(
        label="EC2KeyPair",
        descriptions=(),
        extra_labels=(),
        conditional_labels=(),
        properties=(),
        modules=("aws",),
        schemas=(),
    )
    relationship = Relationship(
        source_label="EC2KeyPair",
        label="MATCHING_FINGERPRINT",
        target_label="EC2KeyPair",
        direction=None,
        descriptions=(),
        properties=(),
        modules=("aws",),
        origins=("analysis",),
        schemas=(),
        analysis_jobs=(),
    )
    model = DataModel(nodes=(node,), relationships=(relationship,))

    # Act
    generated = render_module_schema(model, "aws")

    # Assert
    assert "EC2KeyPair ---|MATCHING_FINGERPRINT| EC2KeyPair" in generated
    assert "(:EC2KeyPair)-[:MATCHING_FINGERPRINT]-(:EC2KeyPair)" in generated
    assert "Source: analysis job" in generated


def test_permission_evaluation_relationships_render_source_and_permissions():
    # Arrange
    definition = PermissionRelationshipDefinition(
        provider="aws",
        source_label="AWSPrincipal",
        target_label="S3Bucket",
        relationship_name="CAN_READ",
        permissions=("S3:GetObject",),
        config_path="cartography/data/permission_relationships.yaml",
    )
    node = Node(
        label="S3Bucket",
        descriptions=(),
        extra_labels=(),
        conditional_labels=(),
        properties=(),
        modules=("aws",),
        schemas=(),
    )
    relationship = Relationship(
        source_label="AWSPrincipal",
        label="CAN_READ",
        target_label="S3Bucket",
        direction=LinkDirection.OUTWARD,
        descriptions=(),
        properties=(),
        modules=("aws",),
        origins=("permission_evaluation",),
        schemas=(),
        analysis_jobs=(),
        permission_relationships=(definition,),
    )
    model = DataModel(
        nodes=(node,),
        relationships=(relationship,),
        permission_relationships=(definition,),
    )

    # Act
    generated = render_module_schema(model, "aws")

    # Assert
    assert "(:AWSPrincipal)-[:CAN_READ]->(:S3Bucket)" in generated
    assert (
        "Source: AWS permission evaluation from "
        "`cartography/data/permission_relationships.yaml`" in generated
    )
    assert "Evaluated permissions: `S3:GetObject`" in generated


def test_ontology_and_cross_module_relationships_are_duplicated_in_module_docs():
    # Arrange
    node = Node(
        label="LastpassUser",
        descriptions=(),
        extra_labels=("UserAccount",),
        conditional_labels=(),
        properties=(),
        modules=("lastpass",),
        schemas=(),
        ontology_labels=("UserAccount",),
    )
    relationships = (
        Relationship(
            source_label="User",
            label="HAS_ACCOUNT",
            target_label="UserAccount",
            direction=LinkDirection.OUTWARD,
            descriptions=(),
            properties=(),
            modules=("ontology",),
            origins=("node_schema",),
            schemas=(),
            analysis_jobs=(),
        ),
        Relationship(
            source_label="Human",
            label="IDENTITY_LASTPASS",
            target_label="LastpassUser",
            direction=LinkDirection.OUTWARD,
            descriptions=(),
            properties=(),
            modules=("analysis",),
            origins=("analysis",),
            schemas=(),
            analysis_jobs=(),
        ),
    )
    model = DataModel(nodes=(node,), relationships=relationships)

    # Act
    generated = render_module_schema(model, "lastpass")

    # Assert
    assert "(:User)-[:HAS_ACCOUNT]->(:UserAccount)" in generated
    assert "(:Human)-[:IDENTITY_LASTPASS]->(:LastpassUser)" in generated


def test_keycloak_schema_doc_is_generated_from_introspected_model():
    # Arrange
    model = inspect_data_model(keycloak_models)

    # Act
    generated = render_module_schema(model, "keycloak")

    # Assert
    assert not Path("docs/root/modules/keycloak/schema.md").exists()
    assert len(model.relationships) == 36
    assert "Represents a Keycloak realm, which is a security domain" in generated
    assert "| name | Yes | The realm name (indexed for queries) |" in generated
    assert (
        "A user inherits membership in the parent groups of its direct groups."
        in generated
    )
    assert "(:KeycloakRole)-[:INDIRECT_GRANTS]->(:KeycloakScope)" in generated
    assert "(:KeycloakAuthenticationFlow)-[:NEXT_STEP]->" in generated
    assert "Deprecated compatibility edge linking a subgroup" in generated
    assert "Deprecated compatibility edge for a role assumed by a user." in generated


def test_workday_schema_doc_is_generated_from_introspected_model():
    # Arrange
    model = inspect_data_model(workday_models)

    # Act
    generated = render_module_schema(model, "workday")

    # Assert
    assert not Path("docs/root/modules/workday/schema.md").exists()
    assert len(model.nodes) == 2
    assert len(model.relationships) == 2
    assert "A person in Workday with the Human label" in generated
    assert "| email | Yes | Work email address indexed" in generated
    assert "(:WorkdayHuman)-[:REPORTS_TO]->(:WorkdayHuman)" in generated
    assert "No description provided." not in generated


def test_workos_schema_doc_is_generated_from_introspected_model():
    # Arrange
    model = inspect_data_model(workos_models)

    # Act
    generated = render_module_schema(model, "workos")

    # Assert
    assert not Path("docs/root/modules/workos/schema.md").exists()
    assert len(model.nodes) == 13
    assert len(model.relationships) == 29
    assert "| slug | Yes | Unique role slug. |" in generated
    assert "role_id" not in generated
    assert "(:WorkOSOrganizationMembership)-[:WITH_ROLE]->(:WorkOSRole)" in generated
    assert "No description provided." not in generated


def test_vercel_schema_doc_is_generated_from_introspected_model():
    # Arrange
    model = inspect_data_model(vercel_models)

    # Act
    generated = render_module_schema(model, "vercel")

    # Assert
    assert not Path("docs/root/modules/vercel/schema.md").exists()
    assert len(model.nodes) == 18
    assert len(model.relationships) == 32
    assert "| action |  | Action performed by the bypass rule. |" in generated
    assert "(:VercelFirewallBypassRule)-[:CREATED_BY]->(:VercelUser)" in generated
    assert "No description provided." not in generated


def test_snipeit_schema_doc_is_generated_from_introspected_model():
    # Arrange
    model = inspect_data_model(snipeit_models)

    # Act
    generated = render_module_schema(model, "snipeit")

    # Assert
    assert not Path("docs/root/modules/snipeit/schema.md").exists()
    assert len(model.nodes) == 3
    assert len(model.relationships) == 5
    assert "A device asset managed by Snipe-IT." in generated
    assert "| serial | Yes | Asset serial number. |" in generated
    assert "Deprecated compatibility edge linking a tenant to its asset." in generated
    assert "No description provided." not in generated


def test_bigfix_schema_doc_is_generated_from_introspected_model():
    # Arrange
    model = inspect_data_model(bigfix_models)

    # Act
    generated = render_module_schema(model, "bigfix")

    # Assert
    assert not Path("docs/root/modules/bigfix/schema.md").exists()
    assert len(model.nodes) == 2
    assert len(model.relationships) == 1
    assert "A computer tracked by BigFix." in generated
    assert "| computername | Yes | Computer name. |" in generated
    assert "(:BigfixRoot)-[:RESOURCE]->(:BigfixComputer)" in generated
    assert "No description provided." not in generated


def test_kandji_schema_doc_is_generated_from_introspected_model():
    # Arrange
    model = inspect_data_model(kandji_models)

    # Act
    generated = render_module_schema(model, "kandji")

    # Assert
    assert not Path("docs/root/modules/kandji/schema.md").exists()
    assert len(model.nodes) == 2
    assert len(model.relationships) == 2
    assert "A device managed by Kandji." in generated
    assert "| serial_number | Yes | Device serial number. |" in generated
    assert "Deprecated compatibility edge linking a device to its tenant." in generated
    assert "No description provided." not in generated


def test_jumpcloud_schema_doc_is_generated_from_introspected_model():
    # Arrange
    model = inspect_data_model(jumpcloud_models)

    # Act
    generated = render_module_schema(model, "jumpcloud")

    # Assert
    assert not Path("docs/root/modules/jumpcloud/schema.md").exists()
    assert len(model.nodes) == 4
    assert len(model.relationships) == 5
    assert "A user account in JumpCloud." in generated
    assert "| jc_system_id | Yes | JumpCloud system ID" in generated
    assert "(:JumpCloudUser)-[:USES]->(:JumpCloudSaaSApplication)" in generated
    assert "No description provided." not in generated


def test_anthropic_schema_doc_is_generated_from_introspected_model():
    # Arrange
    model = inspect_data_model(anthropic_models)

    # Act
    generated = render_module_schema(model, "anthropic")

    # Assert
    assert not Path("docs/root/modules/anthropic/schema.md").exists()
    assert len(model.nodes) == 4
    assert len(model.relationships) == 8
    assert "A user account in an Anthropic organization." in generated
    assert "| display_color |  | Hex color representing the workspace" in generated
    assert "(:AnthropicOrganization)-[:RESOURCE]->(:AnthropicUser)" in generated
    assert "Deprecated compatibility edge for a user that owns an API key." in generated
    assert "No description provided." not in generated


def test_cloudflare_schema_doc_is_generated_from_introspected_model():
    # Arrange
    model = inspect_data_model(cloudflare_models)

    # Act
    generated = render_module_schema(model, "cloudflare")

    # Assert
    assert not Path("docs/root/modules/cloudflare/schema.md").exists()
    assert len(model.nodes) == 5
    assert len(model.relationships) == 5
    assert "A DNS zone managed by Cloudflare." in generated
    assert "| name | Yes | DNS record name. |" in generated
    assert "(:CloudflareMember)-[:HAS_ROLE]->(:CloudflareRole)" in generated
    assert "No description provided." not in generated


def test_subimage_schema_doc_is_generated_from_introspected_model():
    # Arrange
    model = inspect_data_model(subimage_models)

    # Act
    generated = render_module_schema(model, "subimage")

    # Assert
    assert not Path("docs/root/modules/subimage/schema.md").exists()
    assert len(model.nodes) == 6
    assert len(model.relationships) == 5
    assert "A team member in a SubImage tenant." in generated
    assert "| email | Yes | Team member email address. |" in generated
    assert "(:SubImageTenant)-[:RESOURCE]->(:SubImageFramework)" in generated
    assert "No description provided." not in generated


def test_sentry_schema_doc_is_generated_from_introspected_model():
    # Arrange
    model = inspect_data_model(sentry_models)

    # Act
    generated = render_module_schema(model, "sentry")

    # Assert
    assert not Path("docs/root/modules/sentry/schema.md").exists()
    assert len(model.nodes) == 6
    assert len(model.relationships) == 9
    assert "An issue alert rule configured on a Sentry project." in generated
    assert "| require_2fa | Yes | Whether the organization requires" in generated
    assert "(:SentryUser)-[:ADMIN_OF]->(:SentryTeam)" in generated
    assert "No description provided." not in generated


def test_slack_schema_doc_is_generated_from_introspected_model():
    # Arrange
    model = inspect_data_model(slack_models)

    # Act
    generated = render_module_schema(model, "slack")

    # Assert
    assert not Path("docs/root/modules/slack/schema.md").exists()
    assert len(model.nodes) == 5
    assert len(model.relationships) == 13
    assert (
        "| created_by |  | ID of the account that created the user group. |"
        in generated
    )
    assert "(:SlackGroup)-[:MEMBER_OF]->(:SlackChannel)" in generated
    assert "No description provided." not in generated


def test_digitalocean_schema_doc_is_generated_from_introspected_model():
    # Arrange
    model = inspect_data_model(digitalocean_models)

    # Act
    generated = render_module_schema(model, "digitalocean")

    # Assert
    assert not Path("docs/root/modules/digitalocean/schema.md").exists()
    assert len(model.nodes) == 3
    assert len(model.relationships) == 4
    assert "A compute instance in a DigitalOcean project." in generated
    assert "| vpc_uuid |  | UUID of the Droplet's VPC. |" in generated
    assert (
        "Deprecated compatibility edge linking a Droplet to its project." in generated
    )
    assert "No description provided." not in generated


def test_docker_scout_schema_doc_is_generated_from_introspected_model():
    # Arrange
    model = inspect_data_model(docker_scout_models)

    # Act
    generated = render_module_schema(model, "docker_scout")

    # Assert
    assert not Path("docs/root/modules/docker_scout/schema.md").exists()
    assert len(model.nodes) == 2
    assert len(model.relationships) == 3
    assert "current public base image identified by a Docker Scout report" in generated
    assert "(:Image)-[:BUILT_ON]->(:DockerScoutPublicImage)" in generated
    assert (
        "    | benefits | Recommendation benefits reported as a bullet list. |"
        in generated
    )
    assert (
        "    | fix_critical | Number of critical vulnerabilities fixed by the update. |"
        in generated
    )
    assert "    | lastupdated |" not in generated
    assert "    | _sub_resource_label |" not in generated
    assert "No description provided." not in generated


def test_duo_schema_doc_is_generated_from_introspected_model():
    # Arrange
    model = inspect_data_model(duo_models)

    # Act
    generated = render_module_schema(model, "duo")

    # Assert
    assert not Path("docs/root/modules/duo/schema.md").exists()
    assert len(model.nodes) == 7
    assert len(model.relationships) == 13
    assert "| desktoptokens |  | Desktop tokens available to the user. |" in generated
    assert "(:Human)-[:IDENTITY_DUO]->(:DuoUser)" in generated
    assert "No description provided." not in generated


def test_openai_schema_doc_is_generated_from_introspected_model():
    # Arrange
    model = inspect_data_model(openai_models)

    # Act
    generated = render_module_schema(model, "openai")

    # Assert
    assert not Path("docs/root/modules/openai/schema.md").exists()
    assert len(model.nodes) == 6
    assert len(model.relationships) == 15
    assert "An admin API key in an OpenAI organization." in generated
    assert "| email | Yes | User email address. |" in generated
    assert "(:OpenAIOrganization)-[:RESOURCE]->(:OpenAIUser)" in generated
    assert "Deprecated compatibility edge for a service account" in generated
    assert "No description provided." not in generated


def test_oci_schema_doc_is_generated_from_introspected_model():
    # Arrange
    model = inspect_data_model(oci_models)

    # Act
    generated = render_module_schema(model, "oci")

    # Assert
    assert not Path("docs/root/modules/oci/schema.md").exists()
    assert len(model.nodes) == 6
    assert len(model.relationships) == 15
    assert "| email | Yes | User email address. |" in generated
    assert "(:OCIPolicy)-[:OCI_POLICY_REFERENCE]->(:OCIGroup)" in generated
    assert "No description provided." not in generated


def test_pagerduty_schema_doc_is_generated_from_introspected_model():
    # Arrange
    model = inspect_data_model(pagerduty_models)

    # Act
    generated = render_module_schema(model, "pagerduty")

    # Assert
    assert not Path("docs/root/modules/pagerduty/schema.md").exists()
    assert len(model.nodes) == 9
    assert len(model.relationships) == 12
    assert "| support_hours_days_of_week |  | Days of the week included" in generated
    assert "(:PagerDutyUser)-[:MEMBER_OF]->(:PagerDutyTeam)" in generated
    assert "No description provided." not in generated


def test_salesforce_schema_doc_is_generated_from_introspected_model():
    # Arrange
    model = inspect_data_model(salesforce_models)

    # Act
    generated = render_module_schema(model, "salesforce")

    # Assert
    assert not Path("docs/root/modules/salesforce/schema.md").exists()
    assert len(model.nodes) == 7
    assert len(model.relationships) == 13
    assert "A Salesforce user account with the UserAccount label." in generated
    assert "| email | Yes | User email address. |" in generated
    assert "(:SalesforceUser)-[:HAS_ROLE]->(:SalesforceProfile)" in generated
    assert "No description provided." not in generated


def test_spacelift_schema_doc_is_generated_from_introspected_model():
    # Arrange
    model = inspect_data_model(spacelift_models)

    # Act
    generated = render_module_schema(model, "spacelift")

    # Assert
    assert not Path("docs/root/modules/spacelift/schema.md").exists()
    assert len(model.nodes) == 9
    assert len(model.relationships) == 22
    assert (
        "A CloudTrail event from a Spacelift run that interacted with EC2." in generated
    )
    assert "| event_name |  | AWS API action recorded by CloudTrail. |" in generated
    assert "(:CloudTrailSpaceliftEvent)-[:AFFECTED]->(:EC2Instance)" in generated
    assert "No description provided." not in generated


def test_write_module_schema_docs_preserves_manual_pages(
    tmp_path: Path,
):
    # Arrange
    model = inspect_data_model(lastpass_models)
    output_path = tmp_path / "lastpass" / "schema.md"
    output_path.parent.mkdir(parents=True)
    output_path.write_text("Manual schema\n")

    # Act
    write_module_schema_docs(
        model,
        ["lastpass"],
        output_root=tmp_path,
        preserve_existing=True,
    )

    # Assert
    assert output_path.read_text() == "Manual schema\n"


def test_write_module_schema_docs_creates_missing_pages(
    tmp_path: Path,
):
    # Arrange
    model = inspect_data_model(lastpass_models)
    output_path = tmp_path / "lastpass" / "schema.md"

    # Act
    write_module_schema_docs(
        model,
        ["lastpass"],
        output_root=tmp_path,
        preserve_existing=True,
    )

    # Assert
    assert output_path.read_text() == render_module_schema(model, "lastpass")
