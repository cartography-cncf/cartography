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
import cartography.models.gitlab as gitlab_models
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
import cartography.models.sentinelone as sentinelone_models
import cartography.models.sentry as sentry_models
import cartography.models.slack as slack_models
import cartography.models.snipeit as snipeit_models
import cartography.models.socketdev as socketdev_models
import cartography.models.spacelift as spacelift_models
import cartography.models.subimage as subimage_models
import cartography.models.syft as syft_models
import cartography.models.tailscale as tailscale_models
import cartography.models.tenable as tenable_models
import cartography.models.trivy as trivy_models
import cartography.models.vercel as vercel_models
import cartography.models.workday as workday_models
import cartography.models.workos as workos_models
from cartography.models.aws_tagging import AWS_TAGGABLE_RESOURCES
from cartography.models.core.relationships import LinkDirection
from cartography.models.gcp.resource_catalog import GCP_POLICY_BINDING_TARGET_LABELS
from cartography.models.github.repos import _GitHubCollaboratorSchema
from cartography.models.github.repos import GITHUB_COLLABORATOR_SCHEMA_TYPES
from cartography.models.github.repos import make_github_collaborator_schema
from cartography.models.introspection import DataModel
from cartography.models.introspection import inspect_data_model
from cartography.models.introspection import Node
from cartography.models.introspection import PermissionRelationshipDefinition
from cartography.models.introspection import Relationship
from cartography.models.schema_docs import _node_for_module
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
    assert (
        "[`AIModel`](../ontology/schema.html#aimodel) (ontology label) "
        "when `category` equals `model`." in generated
    )
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
    node_headings = [
        line.removeprefix("### ")
        for line in generated.splitlines()
        if line.startswith("### ")
    ]

    # Assert
    assert not Path("docs/root/modules/airbyte/schema.md").exists()
    assert len(model.nodes) == 8
    assert len(model.relationships) == 18
    assert node_headings == sorted(node_headings, key=str.casefold)
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
    assert "(:CrowdstrikeSpotlightVulnerability)-[:HAS_CVE]->(:CVE)" in generated
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
        "(:CrowdstrikeHost)-[:HAS_VULNERABILITY]->"
        "(:CrowdstrikeSpotlightVulnerability)" in generated
    )
    assert "No description provided." not in generated


def test_trivy_schema_doc_is_generated_from_introspected_model():
    # Arrange
    model = inspect_data_model(trivy_models)
    complete_model = inspect_data_model()

    # Act
    generated = render_module_schema(complete_model, "trivy")

    # Assert
    assert not Path("docs/root/modules/trivy/schema.md").exists()
    assert len(model.nodes) == 3
    assert len(model.relationships) == 5
    assert "(:Package)-[:DETECTED_AS]->(:TrivyPackage)" in generated
    assert "(:Package)-[:SHOULD_UPDATE_TO]->(:TrivyFix)" in generated
    assert "(:TrivyImageFinding)-[:AFFECTS]->(:Package)" in generated
    assert "(:CVEMetadata)-[:ENRICHES]->(:CVE)" in generated
    assert (
        "    | version | Package version that fixes the vulnerability. |" in generated
    )
    assert "(:S1AppFinding)-[:LINKED_TO]->(:CVE)" not in generated
    assert "No description provided." not in generated


def test_socketdev_schema_doc_is_generated_from_introspected_model():
    # Arrange
    model = inspect_data_model(socketdev_models)
    complete_model = inspect_data_model()

    # Act
    generated = render_module_schema(complete_model, "socketdev")

    # Assert
    assert not Path("docs/root/modules/socketdev/schema.md").exists()
    assert len(model.nodes) == 5
    assert len(model.relationships) == 9
    assert "## Socket.dev Schema" in generated
    assert "(:Package)-[:DETECTED_AS]->(:SocketDevDependency)" in generated
    assert "(:SocketDevRepository)-[:MONITORS]->(:CodeRepository)" in generated
    assert "| ghsa_id | Yes | GitHub Security Advisory identifier. |" in generated
    assert "No description provided." not in generated


def test_sentinelone_schema_doc_is_generated_from_introspected_model():
    # Arrange
    model = inspect_data_model(sentinelone_models)
    complete_model = inspect_data_model()

    # Act
    generated = render_module_schema(complete_model, "sentinelone")

    # Assert
    assert not Path("docs/root/modules/sentinelone/schema.md").exists()
    assert len(model.nodes) == 5
    assert len(model.relationships) == 9
    assert "## SentinelOne Schema" in generated
    assert "(:Device)-[:OBSERVED_AS]->(:S1Agent)" in generated
    assert "(:S1AppFinding)-[:AFFECTS]->(:Device)" in generated
    assert "(:CVEMetadata)-[:ENRICHES]->(:CVE)" in generated
    assert (
        "    | installeddatetime | Timestamp when the application version was "
        "installed. |" in generated
    )
    assert (
        "    | installationpath | File system path where the application version "
        "is installed. |" in generated
    )
    assert "(:CVE)-[:LINKED_TO]->(:SemgrepSCAFinding)" not in generated
    assert "No description provided." not in generated


def test_tenable_schema_doc_is_generated_from_introspected_model():
    # Arrange
    model = inspect_data_model(tenable_models)
    complete_model = inspect_data_model()

    # Act
    generated = render_module_schema(complete_model, "tenable")

    # Assert
    assert not Path("docs/root/modules/tenable/schema.md").exists()
    assert len(model.nodes) == 11
    assert len(model.relationships) == 20
    assert "`CVE` when `has_cve` equals `true`." in generated
    assert "(:CVEMetadata)-[:ENRICHES]->(:CVE)" in generated
    assert "| cve_list | Yes | CVE IDs associated with the finding. |" in generated
    assert "Deprecated compatibility edge" in generated
    assert "(:TenableFinding)-[:DETECTED_BY]->(:TenablePlugin)" in generated
    assert "No description provided." not in generated


def test_gitlab_schema_doc_is_generated_from_introspected_model():
    # Arrange
    model = inspect_data_model(gitlab_models)
    complete_model = inspect_data_model()

    # Act
    generated = render_module_schema(complete_model, "gitlab")
    mermaid_graph = generated.split("graph LR", 1)[1].split("```", 1)[0]

    # Assert
    assert not Path("docs/root/modules/gitlab/schema.md").exists()
    assert len(model.nodes) == 17
    assert len(model.relationships) == 46
    assert mermaid_graph.count("-->") == 75
    assert "(:TrivyImageFinding)-[:AFFECTS]->(:Image)" in generated
    assert "(:SyftPackage)-[:DEPLOYED]->(:Image)" in generated
    assert "(:Image)-[:PACKAGED_FROM]->(:GitHubRepository)" in generated
    assert "(:SocketDevRepository)-[:MONITORS]->(:CodeRepository)" in generated
    assert "(:Image)-[:PACKAGED_BY]->(:GitHubWorkflow)" not in generated
    assert (
        "| masked_and_hidden |  | Whether the value is masked and cannot be "
        "retrieved after creation. |" in generated
    )
    assert (
        "    | command_similarity | Similarity score between image build commands "
        "and Dockerfile commands. |" in generated
    )
    assert "No description provided." not in generated


def test_github_schema_doc_is_generated_from_full_introspected_model():
    # Arrange
    complete_model = inspect_data_model()
    github_model = complete_model.for_module("github")
    collaborator_labels = {
        f"{affiliation}_COLLAB_{permission}"
        for affiliation in ("DIRECT", "OUTSIDE")
        for permission in ("ADMIN", "MAINTAIN", "READ", "TRIAGE", "WRITE")
    }

    # Act
    generated = render_module_schema(complete_model, "github")
    runtime_collaborator_schemas = {
        label: make_github_collaborator_schema(label) for label in collaborator_labels
    }
    fallback_schema = make_github_collaborator_schema("CUSTOM_COLLAB_ROLE")

    # Assert
    assert not Path("docs/root/modules/github/schema.md").exists()
    assert len(github_model.nodes) == 25
    assert len(github_model.relationships) == 85
    assert set(GITHUB_COLLABORATOR_SCHEMA_TYPES) == collaborator_labels
    assert all(
        type(runtime_collaborator_schemas[label])
        is GITHUB_COLLABORATOR_SCHEMA_TYPES[label]
        for label in collaborator_labels
    )
    assert {
        schema.other_relationships.rels[0].rel_label
        for schema in runtime_collaborator_schemas.values()
    } == collaborator_labels
    assert type(fallback_schema) is _GitHubCollaboratorSchema
    assert fallback_schema.rel_label == "CUSTOM_COLLAB_ROLE"
    assert fallback_schema.other_relationships.rels[0].rel_label == "CUSTOM_COLLAB_ROLE"
    assert collaborator_labels <= {
        relationship.label for relationship in github_model.relationships
    }
    assert "A source code repository hosted in GitHub." in generated
    assert "| defaultbranch |  | Default branch name. |" in generated
    assert (
        "| source |  | Version source: `dependency_graph` for GitHub data or "
        "`lockfile` for lockfile fallback. |" in generated
    )
    assert (
        "| trigger_events |  | Trigger event names parsed from workflow YAML. |"
        in generated
    )
    assert (
        "| permissions |  | Fine-grained PAT permission details encoded as JSON. |"
        in generated
    )
    assert (
        "| diff_id | Yes | Uncompressed layer content digest used for "
        "deduplication. |" in generated
    )
    assert (
        "    | confidence | Parent image match confidence from 0.0 (lowest) "
        "to 1.0 (highest). |" in generated
    )
    assert "| parameters |  | Complete rule parameters encoded as JSON. |" in generated
    assert (
        "| owner_logins |  | GitHub user logins parsed from `@user` owners. |"
        in generated
    )
    assert (
        "    | commit_count | Number of commits observed in the last 30 days. |"
        in generated
    )
    assert "Links a GitHub repository to an Actions secret." in generated
    assert "Links a GitHub repository to an Actions variable." in generated
    assert (
        "A GitHub Actions secret at organization, repository, or environment scope."
        in generated
    )
    assert (
        "A digest-addressed container image or manifest list stored in GitHub "
        "Container Registry." in generated
    )
    assert (
        "[`Image`](../ontology/schema.html#image) (ontology label) "
        "when `type` equals `image`." in generated
    )
    assert (
        "[`ImageManifestList`](../ontology/schema.html#imagemanifestlist) "
        "(ontology label) when `type` equals `manifest_list`." in generated
    )
    assert (
        "[`CVE`](../ontology/schema.html#cve) (ontology label) "
        "when `has_cve` equals `true`." in generated
    )
    assert (
        "**Ontology Projection**: `Dependency` contributes data to canonical "
        "[`Package`](../ontology/schema.html#package) nodes." in generated
    )
    assert "(:AWSLambda)-[:HAS_IMAGE]->(:GitHubContainerImage)" in generated
    assert "(:KubernetesContainer)-[:HAS_IMAGE]->(:GitHubContainerImage)" in generated
    assert "(:Image)-[:PACKAGED_FROM]->(:GitHubRepository)" in generated
    assert "(:SocketDevRepository)-[:MONITORS]->(:CodeRepository)" in generated
    assert "(:S1AppFinding)-[:LINKED_TO]->(:CVE)" not in generated
    assert (
        "    | command_similarity | Similarity score between image build commands "
        "and Dockerfile commands. |" in generated
    )
    assert "No description provided." not in generated


def test_gcp_schema_doc_is_generated_from_full_introspected_model():
    complete_model = inspect_data_model()
    gcp_model = complete_model.for_module("gcp")
    artifact_registry_guide = Path(
        "docs/root/modules/gcp/artifact-registry.md"
    ).read_text()
    cloud_run_guide = Path("docs/root/modules/gcp/cloud-run.md").read_text()
    module_index = Path("docs/root/modules/gcp/index.md").read_text()

    generated = render_module_schema(complete_model, "gcp")
    relationship_shapes = {
        (
            relationship.source_label,
            relationship.label,
            relationship.target_label,
        )
        for relationship in gcp_model.relationships
    }
    permission_relationships = tuple(
        relationship
        for relationship in gcp_model.relationships
        if relationship.permission_relationships
    )

    assert not Path("docs/root/modules/gcp/schema.md").exists()
    assert artifact_registry_guide.count("```cypher") == 3
    assert "Image -->|CONTAINS| ImageLayer" not in artifact_registry_guide
    assert "expanded into one" in artifact_registry_guide
    assert "repository-scoped, pullable image identity" in artifact_registry_guide
    assert "Google Cloud Run is a serverless compute platform" in cloud_run_guide
    assert "Service -->|CONTAINS| ServiceContainer" in cloud_run_guide
    assert "Service -->|WORKLOAD_PARENT| ServiceContainer" in cloud_run_guide
    assert "Job -->|CONTAINS| JobContainer" in cloud_run_guide
    assert "Job -->|WORKLOAD_PARENT| JobContainer" in cloud_run_guide
    assert "HAS_CONTAINER" not in cloud_run_guide
    assert "artifact-registry" in module_index
    assert "cloud-run" in module_index
    assert len(gcp_model.nodes) == 68
    assert len(gcp_model.relationships) == 209
    assert not any(
        "GCPResource" in (source_label, target_label)
        for source_label, _, target_label in relationship_shapes
    )
    assert {
        target_label
        for source_label, relationship_label, target_label in relationship_shapes
        if source_label == "GCPPolicyBinding" and relationship_label == "APPLIES_TO"
    } == set(GCP_POLICY_BINDING_TARGET_LABELS)
    assert len(permission_relationships) == 15
    assert all(
        {
            "has_condition",
            "condition_title",
            "condition_expression",
        }
        <= {prop.name for prop in relationship.properties}
        for relationship in permission_relationships
    )
    assert (
        "> **Ontology Mapping**: Some schema variants may also use the ontology "
        "label [`Tag`](../ontology/schema.html#tag)." in generated
    )
    assert (
        "> **Additional Labels**: Some schema variants may also use "
        "`GCPBucketLabel`." in generated
    )
    assert (
        "> **Ontology Mapping**: Some schema variants may also use the ontology "
        "label [`Subnet`](../ontology/schema.html#subnet)." in generated
    )
    assert (
        "> **Ontology Mapping**: This node uses the ontology label "
        "[`ImageLayer`](../ontology/schema.html#imagelayer)." in generated
    )
    assert (
        "[`ImageAttestation`](../ontology/schema.html#imageattestation) "
        "(ontology label) when `type` equals `attestation`." in generated
    )
    assert (
        "[`ImageManifestList`](../ontology/schema.html#imagemanifestlist) "
        "(ontology label) when `type` equals `manifest_list`." in generated
    )
    assert (
        "| machine_type |  | The instance machine type short name, "
        "e.g. `n2d-standard-4`. |" in generated
    )
    assert (
        "| database_engine |  | Database engine family derived from "
        "database_version, such as MYSQL, POSTGRES, or SQLSERVER. |" in generated
    )
    assert (
        "| disk_size_gb |  | Provisioned data disk capacity in gigabytes, "
        "derived from settings.dataDiskSizeGb. |" in generated
    )
    assert (
        "| diff_id |  | Uncompressed OCI layer digest from rootfs.diff_ids; "
        "compressed manifest digest and size are not stored. |" in generated
    )
    assert (
        "Parent-image evidence strength; digest-verified SBOM matches use "
        "`explicit`." in generated
    )
    assert (
        "Binding identifier in `{resource}_{role}` form. Conditional bindings "
        "append `_{hash}`" in generated
    )
    assert "(:TrivyImageFinding)-[:AFFECTS]->(:Image)" in generated
    assert "(:Package)-[:DEPLOYED]->(:Image)" in generated
    assert "(:GCPVpc)-[:RESOURCE]->(:GCPSubnet)" not in generated
    assert "No description provided." not in generated
    assert not any(
        "Value reported by the Google Cloud API for this resource." in path.read_text()
        for path in Path("cartography/models/gcp").rglob("*.py")
    )


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
        "> **Ontology Mapping**: This node uses the ontology label "
        "[`UserAccount`](../ontology/schema.html#useraccount)." in generated
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
        "[`Device`](../ontology/schema.html#device) nodes." in generated
    )
    assert (
        "**Ontology Projection**: `JamfMobileDevice` contributes data to canonical "
        "[`Device`](../ontology/schema.html#device) nodes." in generated
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


def test_microsoft_schema_doc_is_generated_from_full_introspected_model():
    # Arrange
    complete_model = inspect_data_model()
    microsoft_model = complete_model.for_module("microsoft")

    # Act
    generated = render_module_schema(complete_model, "microsoft")
    azure_tenant = complete_model.get_node("AzureTenant")

    # Assert
    assert not Path("docs/root/modules/microsoft/schema.md").exists()
    assert len(microsoft_model.nodes) == 12
    assert len(microsoft_model.relationships) == 29
    assert "### AzureTenant" in generated
    assert "**Additional Labels**: This node also uses `EntraTenant`." in generated
    assert "### EntraTenant" not in generated
    assert azure_tenant is not None
    assert "EntraTenant" not in _node_for_module(azure_tenant, "azure").extra_labels
    assert "| id | Yes | Microsoft tenant ID. |" in generated
    assert "| device_name | Yes | Name of the managed device. |" in generated
    assert (
        "**Ontology Projection**: `IntuneManagedDevice` contributes data "
        "to canonical [`Device`](../ontology/schema.html#device) nodes." in generated
    )
    assert "(:Device)-[:OBSERVED_AS]->(:IntuneManagedDevice)" in generated
    assert (
        "Analysis job `Intune compliance policy to device resolution` generates "
        "`(:IntuneCompliancePolicy)-[:APPLIES_TO]->(:IntuneManagedDevice)`."
        in generated
    )
    assert "Source:" not in generated
    assert "(:EntraUser)-[:CAN_READ]->(:AzureSQLServer)" in generated
    assert "(:EntraUser)-[:CAN_SIGN_ON_TO]->(:AWSSSOUser)" in generated
    assert (
        "(:GCPBigQueryConnection)-[:CONNECTS_WITH]->(:EntraServicePrincipal)"
        in generated
    )
    assert "No description provided." not in generated


def test_scaleway_schema_doc_is_generated_from_full_introspected_model():
    # Arrange
    complete_model = inspect_data_model()
    scaleway_model = complete_model.for_module("scaleway")

    # Act
    generated = render_module_schema(complete_model, "scaleway")
    security_group_rule = scaleway_model.get_node("ScalewaySecurityGroupRule")

    # Assert
    assert not Path("docs/root/modules/scaleway/schema.md").exists()
    assert len(scaleway_model.nodes) == 55
    assert len(scaleway_model.relationships) == 105
    assert "Represents the digest-addressed image content" in generated
    assert "| source_uri | Yes | Source VCS repository URL" in generated
    assert (
        "Connects `ScalewayFlexibleIp` to `ScalewayInstance` through `IDENTIFIES`."
        in generated
    )
    assert "(:ScalewayFlexibleIp)-[:IDENTIFIES]->(:ScalewayInstance)" in generated
    assert security_group_rule is not None
    assert security_group_rule.extra_labels == ("IpRule",)
    assert {
        (label.label, tuple(sorted(label.conditions.items())))
        for label in security_group_rule.conditional_labels
    } == {
        ("IpPermissionEgress", (("direction", "outbound"),)),
        ("IpPermissionInbound", (("direction", "inbound"),)),
    }
    assert "(:Container)-[:RESOLVED_IMAGE]->(:Image)" in generated
    assert "(:Image)-[:PACKAGED_FROM]->(:GitHubRepository)" in generated
    assert "(:PublicIP)-[:RESERVED_BY]->(:ScalewayFlexibleIp)" in generated
    assert (
        "(:AzureApplicationGatewayBackendPool)-[:ROUTES_TO]->(:DNSRecord)" in generated
    )
    assert "(:LoadBalancer)-[:EXPOSE]->(:Container)" not in generated
    assert "(:Image)-[:PACKAGED_BY]->(:GitHubWorkflow)" not in generated
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
    assert "Source:" not in generated


def test_permission_evaluation_relationships_render_permissions_without_source():
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
        descriptions=("Allows an AWS principal to read objects from an S3 bucket.",),
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
    assert "Allows an AWS principal to read objects from an S3 bucket." in generated
    assert "(:AWSPrincipal)-[:CAN_READ]->(:S3Bucket)" in generated
    assert "Source:" not in generated
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


def test_ontology_schema_doc_is_generated_from_introspected_catalog():
    # Arrange
    model = inspect_data_model()

    # Act
    generated = render_module_schema(model, "ontology")
    node_headings = [
        line.removeprefix("### ")
        for line in generated.splitlines()
        if line.startswith("### ")
    ]

    # Assert
    assert not Path("docs/root/modules/ontology/schema.md").exists()
    assert "### User" in generated
    assert "### Device" in generated
    assert "### PublicIP" in generated
    assert "### Package" in generated
    assert "### UserAccount" in generated
    assert "### ImageTag" in generated
    assert node_headings == sorted(node_headings, key=str.casefold)
    assert "**Abstract Ontology Node**" in generated
    assert "**Semantic Label**" in generated
    assert (
        "| *_ont_active* | Yes | Normalized active for nodes carrying "
        "`UserAccount`. |" in generated
    )
    assert "No normalized properties are defined for this semantic label." in generated
    for constraint in model.ontology_relationship_constraints:
        assert (
            f"(:{constraint.source_label})-[:{constraint.label}]->"
            f"(:{constraint.target_label})"
        ) in generated
    assert "Source:" not in generated
    assert "No description provided." not in generated


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


def test_semgrep_schema_doc_is_generated_from_introspected_model():
    # Arrange
    complete_model = inspect_data_model()
    semgrep_model = complete_model.for_module("semgrep")

    # Act
    generated = render_module_schema(complete_model, "semgrep")

    # Assert
    assert not Path("docs/root/modules/semgrep/schema.md").exists()
    assert len(semgrep_model.nodes) == 8
    assert len(semgrep_model.relationships) == 22
    assert (
        "A code-level security issue reported by Semgrep Cloud or Semgrep OSS."
        in generated
    )
    assert (
        "| repository_url |  | Full URL of the repository where the finding was discovered. |"
        in generated
    )
    assert (
        "> **Ontology Projection**: `SemgrepGoLibrary` contributes data "
        "to canonical [`Package`](../ontology/schema.html#package) nodes." in generated
    )
    assert (
        "> **Ontology Projection**: `SemgrepNpmLibrary` contributes data "
        "to canonical [`Package`](../ontology/schema.html#package) nodes." in generated
    )
    assert "(:Package)-[:DETECTED_AS]->(:SemgrepDependency)" in generated
    assert "(:SemgrepSCAFinding)-[:AFFECTS]->(:Package)" in generated
    assert (
        "    | specifier | Version specifier required by the repository. |" in generated
    )
    assert "No description provided." not in generated


def test_kubernetes_schema_doc_is_generated_from_full_introspected_model():
    # Arrange
    complete_model = inspect_data_model()
    kubernetes_model = complete_model.for_module("kubernetes")

    # Act
    generated = render_module_schema(complete_model, "kubernetes")

    # Assert
    assert not Path("docs/root/modules/kubernetes/schema.md").exists()
    assert len(kubernetes_model.nodes) == 19
    assert len(kubernetes_model.relationships) == 72
    assert "A Kubernetes pod and its workload security configuration." in generated
    assert (
        "| kubeconfig_tls_configuration_status |  | "
        "Derived kubeconfig TLS posture (`valid_config`, `insecure_skip_tls`, "
        "`missing_ca_material`, `unknown`). |"
    ) in generated
    assert (
        "    | mount_method | How the pod consumes the secret: volume, "
        "environment, or both. |"
    ) in generated
    assert "(:KubernetesPod)-[:USES_SECRET]->(:KubernetesSecret)" in generated
    assert "(:AIBOMSource)-[:RUNS_ON]->(:Container)" in generated
    assert "(:Container)-[:RESOLVED_IMAGE]->(:Image)" in generated
    assert "(:LoadBalancer)-[:EXPOSE]->(:Container)" not in generated
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


def test_aws_schema_doc_groundwork_is_complete_while_manual_page_is_preserved():
    complete_model = inspect_data_model()
    aws_model = complete_model.for_module("aws")
    module_index = Path("docs/root/modules/aws/index.md").read_text()

    generated = render_module_schema(complete_model, "aws")
    relationship_shapes = {
        (
            relationship.source_label,
            relationship.label,
            relationship.target_label,
        )
        for relationship in aws_model.relationships
    }
    tagging_sources = {
        relationship.source_label
        for relationship in aws_model.relationships
        if relationship.label == "TAGGED" and relationship.target_label == "AWSTag"
    }
    permission_relationships = tuple(
        relationship
        for relationship in aws_model.relationships
        if relationship.permission_relationships
    )

    assert Path("docs/root/modules/aws/schema.md").exists()
    assert {
        "organizations",
        "infrastructure-investigations",
        "container-images",
        "identity-access",
        "tagging-and-labels",
    } <= set(module_index.splitlines())
    assert len(aws_model.nodes) == 166
    assert len(aws_model.relationships) == 469
    assert tagging_sources == {resource.label for resource in AWS_TAGGABLE_RESOURCES}
    assert len(permission_relationships) == 12
    assert (
        "AWSPrincipal",
        "CAN_START_SESSION",
        "AWSEC2Instance",
    ) in relationship_shapes
    assert not any("AWSVpnGateway" in shape for shape in relationship_shapes)
    assert (
        "Target precondition: "
        "`(:AWSEC2Instance)-[:HAS_INFORMATION]->"
        "(:AWSSSMInstanceInformation)` must exist"
    ) in generated
    assert "(:DNSRecord)-[:DNS_POINTS_TO]->(:AWSEC2Instance)" in generated
    assert "(:LoadBalancer)-[:EXPOSE]->(:Container)" in generated
    assert "(:AzureContainerInstance)-[:HAS_IMAGE]->(:AWSECRImage)" in generated
    assert "(:DNSRecord)-[:DNS_POINTS_TO]->(:AzureFunctionApp)" not in generated
    assert "(:Image)-[:PACKAGED_FROM]->(:GitHubRepository)" not in generated
    assert "(:TailscaleDevice)-[:IS_INSTANCE]->(:ComputeInstance)" not in generated
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
    assert "(:SpaceliftCloudTrailEvent)-[:AFFECTED]->(:AWSEC2Instance)" in generated
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
