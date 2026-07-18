import logging
from typing import Dict
from typing import List
from typing import Set

import pytest

import cartography.models
from cartography.intel.aws.label_migrations import AWS_LABEL_MIGRATIONS
from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ConditionalNodeLabel
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import MatchLinkSubResource
from tests.utils import load_models

logger = logging.getLogger(__name__)

# Relationship endpoints that are intentionally supplied by legacy loaders,
# dynamic permission nodes, or optional modules rather than node schemas.
RELATION_ONLY_NODE_LABELS: Set[str] = {
    "AWSVpnGateway",
    "AzureResource",
    "AzureVirtualHub",
    "EntraPrincipal",
    "GCPResource",
    "OktaGroup",
    "OktaUser",
}

PROVIDER_PREFIX_EXCEPTIONS: Dict[str, Set[str]] = {
    "cartography.models.github": {
        "ProgrammingLanguage",
        "PythonLibrary",
    },
}

MIGRATED_PROVIDER_LABELS: Dict[str, Dict[str, str]] = {
    "cartography.models.github": {
        "GitHubDependencyGraphManifest": "DependencyGraphManifest",
    },
    "cartography.models.semgrep": {
        "SemgrepGoLibrary": "GoLibrary",
        "SemgrepNpmLibrary": "NpmLibrary",
    },
    "cartography.models.crowdstrike": {
        "CrowdstrikeSpotlightVulnerability": "SpotlightVulnerability",
    },
    "cartography.models.spacelift": {
        "SpaceliftCloudTrailEvent": "CloudTrailSpaceliftEvent",
    },
}

PREEXISTING_AWS_LABEL_MIGRATIONS: set[tuple[str, str]] = {
    ("DNSRecord", "AWSDNSRecord"),
    ("DNSZone", "AWSDNSZone"),
    ("IpPermissionInbound", "AWSIpPermissionInbound"),
    ("IpRange", "AWSIpRange"),
    ("IpRule", "AWSIpRule"),
    ("LoadBalancer", "AWSLoadBalancer"),
    ("LoadBalancerV2", "AWSLoadBalancerV2"),
    ("MfaDevice", "AWSMfaDevice"),
    ("Tag", "AWSTag"),
}


def test_model_objects_naming_convention():
    """Test that all model objects follow the naming convention."""
    errors: List[str] = []
    for module_name, element in load_models(cartography.models):
        if issubclass(element, CartographyNodeSchema):
            if not element.__name__.endswith("Schema"):
                errors.append(f"Node {element.__name__}: name must end with 'Schema'.")
        elif issubclass(element, CartographyRelSchema):
            if not element.__name__.endswith("Rel") and not element.__name__.endswith(
                "MatchLink"
            ):
                errors.append(
                    f"Relationship {element.__name__}: name must end with 'Rel' or 'MatchLink'."
                )
        elif issubclass(element, CartographyNodeProperties):
            if not element.__name__.endswith("Properties"):
                errors.append(
                    f"Node properties {element.__name__}: name must end with 'Properties'."
                )
        elif issubclass(element, CartographyRelProperties):
            if not element.__name__.endswith(
                "RelProperties"
            ) and not element.__name__.endswith("MatchLinkProperties"):
                errors.append(
                    f"Relationship properties {element.__name__}: name must end with 'RelProperties' or 'MatchLinkProperties'."
                )
    assert not errors, "Naming convention violations:\n  - " + "\n  - ".join(errors)


def test_microsoft_tenant_relationships_target_azure_tenant():
    """Ensure model introspection uses one canonical Microsoft tenant vertex."""
    errors: list[str] = []
    for module_name, element in load_models(cartography.models):
        if not module_name.startswith("cartography.models.microsoft"):
            continue
        if not issubclass(element, CartographyRelSchema):
            continue

        relationship = element()
        if relationship.target_node_label == "EntraTenant":
            errors.append(f"{module_name}.{element.__name__}.target_node_label")

        for scope_name in ("source_node_sub_resource", "target_node_sub_resource"):
            scope = getattr(relationship, scope_name, None)
            if scope and scope.target_node_label == "EntraTenant":
                errors.append(f"{module_name}.{element.__name__}.{scope_name}")

    assert not errors, (
        "Microsoft relationships must target the canonical AzureTenant label:\n  - "
        + "\n  - ".join(errors)
    )


def test_aws_primary_node_labels_use_provider_prefix():
    errors: List[str] = []
    for module_name, element in load_models(cartography.models):
        if module_name != "cartography.models.aws":
            continue
        if not issubclass(element, CartographyNodeSchema):
            continue
        if element.label.startswith("AWS"):
            continue
        errors.append(
            f"{element.__name__} uses unprefixed AWS label {element.label!r}.",
        )

    assert not errors, "AWS node label prefix violations:\n  - " + "\n  - ".join(errors)


def test_migrated_aws_labels_keep_legacy_alias_until_v1():
    migrations_by_new_label = {
        migration.new_label: migration.old_label for migration in AWS_LABEL_MIGRATIONS
    }
    errors: List[str] = []

    for module_name, element in load_models(cartography.models):
        if module_name != "cartography.models.aws":
            continue
        if not issubclass(element, CartographyNodeSchema):
            continue
        old_label = migrations_by_new_label.get(element.label)
        if old_label is None:
            continue
        node_schema = element()
        extra_labels = (
            node_schema.extra_node_labels.labels
            if node_schema.extra_node_labels is not None
            else []
        )
        if old_label not in extra_labels:
            errors.append(
                f"{element.__name__} must keep {old_label!r} as an alias "
                "until v1.0.0.",
            )

    assert not errors, "Missing AWS compatibility aliases:\n  - " + "\n  - ".join(
        errors
    )


def test_aws_label_migration_registry_matches_model_aliases():
    registered_pairs = {
        (migration.old_label, migration.new_label) for migration in AWS_LABEL_MIGRATIONS
    }
    discovered_pairs: set[tuple[str, str]] = set()

    for module_name, element in load_models(cartography.models):
        if module_name != "cartography.models.aws":
            continue
        if not issubclass(element, CartographyNodeSchema):
            continue

        node_schema = element()
        extra_labels = (
            node_schema.extra_node_labels.labels
            if node_schema.extra_node_labels is not None
            else []
        )
        for extra_label in extra_labels:
            if (
                isinstance(extra_label, str)
                and node_schema.label == f"AWS{extra_label}"
            ):
                discovered_pairs.add((extra_label, node_schema.label))

    assert discovered_pairs == registered_pairs | PREEXISTING_AWS_LABEL_MIGRATIONS


@pytest.mark.parametrize(
    ("module_name", "prefix"),
    [
        ("cartography.models.github", "GitHub"),
        ("cartography.models.semgrep", "Semgrep"),
        ("cartography.models.crowdstrike", "Crowdstrike"),
        ("cartography.models.spacelift", "Spacelift"),
    ],
)
def test_provider_primary_node_labels_use_provider_prefix(module_name, prefix):
    errors: List[str] = []
    exceptions = PROVIDER_PREFIX_EXCEPTIONS.get(module_name, set())
    for loaded_module_name, element in load_models(cartography.models):
        if loaded_module_name != module_name:
            continue
        if not issubclass(element, CartographyNodeSchema):
            continue
        if element.label.startswith(prefix) or element.label in exceptions:
            continue
        errors.append(
            f"{element.__name__} uses unprefixed {prefix} label {element.label!r}.",
        )

    assert not errors, f"{prefix} node label prefix violations:\n  - " + "\n  - ".join(
        errors
    )


def test_migrated_provider_labels_keep_legacy_alias_until_v1():
    errors: List[str] = []
    for module_name, element in load_models(cartography.models):
        if not issubclass(element, CartographyNodeSchema):
            continue
        old_label = MIGRATED_PROVIDER_LABELS.get(module_name, {}).get(element.label)
        if old_label is None:
            continue
        node_schema = element()
        extra_labels = (
            node_schema.extra_node_labels.labels
            if node_schema.extra_node_labels is not None
            else []
        )
        if old_label not in extra_labels:
            errors.append(
                f"{element.__name__} must keep {old_label!r} as an alias "
                "until v1.0.0.",
            )

    assert not errors, "Missing provider compatibility aliases:\n  - " + "\n  - ".join(
        errors
    )


def test_relationship_endpoint_labels_are_registered():
    model_objects = list(load_models(cartography.models))
    registered_labels: Set[str] = set(RELATION_ONLY_NODE_LABELS)

    for _, element in model_objects:
        if not issubclass(element, CartographyNodeSchema):
            continue
        node_schema = element()
        registered_labels.add(node_schema.label)
        if node_schema.extra_node_labels is None:
            continue
        for extra_label in node_schema.extra_node_labels.labels:
            if isinstance(extra_label, ConditionalNodeLabel):
                registered_labels.add(extra_label.label)
            else:
                registered_labels.add(extra_label)

    errors: List[str] = []
    for module_name, element in model_objects:
        if not issubclass(element, CartographyRelSchema):
            continue
        rel_schema = element()
        for endpoint_name, label in (
            ("source", rel_schema.source_node_label),
            ("target", rel_schema.target_node_label),
        ):
            if label is not None and label not in registered_labels:
                errors.append(
                    f"{module_name}.{element.__name__} has unknown "
                    f"{endpoint_name} label {label!r}.",
                )

    assert not errors, "Unknown relationship endpoint labels:\n  - " + "\n  - ".join(
        errors
    )


def test_relationship_endpoints_do_not_use_migrated_aws_labels():
    legacy_labels = {migration.old_label for migration in AWS_LABEL_MIGRATIONS}
    errors: list[str] = []

    for module_name, element in load_models(cartography.models):
        if not issubclass(element, CartographyRelSchema):
            continue
        relationship = element()
        for endpoint_name, label in (
            ("source", relationship.source_node_label),
            ("target", relationship.target_node_label),
        ):
            if label in legacy_labels:
                errors.append(
                    f"{module_name}.{element.__name__} uses legacy "
                    f"{endpoint_name} label {label!r}.",
                )

        for scope_name in ("source_node_sub_resource", "target_node_sub_resource"):
            scope = getattr(relationship, scope_name, None)
            if scope and scope.target_node_label in legacy_labels:
                errors.append(
                    f"{module_name}.{element.__name__}.{scope_name} uses legacy "
                    f"label {scope.target_node_label!r}.",
                )

    assert not errors, "Legacy AWS relationship endpoint labels:\n  - " + "\n  - ".join(
        errors
    )


# Node labels whose sub_resource_relationship intentionally uses a non-RESOURCE
# rel_label. These are accepted exceptions; new modules should still default to
# 'RESOURCE' and only be added here after explicit review.
SUB_RESOURCE_REL_LABEL_EXCEPTIONS: Set[str] = {
    # AWSPolicyStatement is scoped to its parent AWSPolicy via STATEMENT rather
    # than RESOURCE. Statement IDs of AWS-managed policies are global (the same
    # statement is shared by every account that attaches the policy), so making
    # the account the cleanup scope would risk a delete in account A removing a
    # statement still referenced by account B; the per-policy STATEMENT scope
    # avoids that cross-account interference.
    "AWSPolicyStatement",
}

# Modules whose APIs do not expose a single tenant root that could anchor every
# node, so the "multiple root nodes" check is skipped for them. Mostly scanner
# integrations that ingest flat lists of findings without a containing tenant
# entity.
MODULES_WITHOUT_TENANT_ROOT: Set[str] = {
    "cartography.models.aibom",
    "cartography.models.pagerduty",
    "cartography.models.trivy",
}

# Node labels that are intentionally global / shared and therefore have no
# sub_resource_relationship. They are not flagged as extra root nodes by
# test_sub_resource_relationship.
GLOBAL_NODE_LABELS: Set[str] = {
    # Ontology canonical nodes — explicitly cross-tenant by design.
    "Device",
    "Package",
    "PublicIP",
    "User",
    # AWS-owned / cross-account resources.
    "AWSCidrBlock",
    "AWSManagedPolicy",
    # AWS-managed public SSM parameters are regional catalog data shared by
    # every account, so they must not be owned or cleaned up per AWSAccount.
    "AWSPublicSSMParameter",
    "AWSServicePrincipal",
    "AWSTag",
    # CVE records ingested by CrowdStrike are public CVEs shared across tenants;
    # CrowdstrikeCVESchema sets scoped_cleanup=False explicitly.
    "CrowdstrikeFinding",
    # Public/global registry data.
    "DockerScoutPublicImage",
    "DockerScoutPublicImageTag",
    # GCP Artifact Registry images are a shared canonical container-image node
    # whose tenancy is set dynamically through a MatchLink
    # (`_sub_resource_label`/`_sub_resource_id` kwargs) rather than a fixed
    # sub_resource_relationship, so the label legitimately has no static root.
    "GCPArtifactRegistryImage",
    # GitHub nodes that can exist outside any organization. A GitHubUser may
    # be unaffiliated, and a GitHubRepository can be owned by a personal user
    # rather than an organization, so neither is anchored to a single tenant.
    "GitHubRepository",
    "GitHubUser",
    # Shared GitHub nodes (cross-org / cross-repo). GitHubDependency uses a
    # global `name|requirements` id and is referenced by repos across orgs, so
    # it uses unscoped cleanup like PythonLibrary.
    "GitHubDependency",
    "ProgrammingLanguage",
    "PythonLibrary",
    # Workday canonical human (mirrors the ontology pattern).
    "WorkdayHuman",
}

ADDITIONAL_TOP_LEVEL_TENANT_LABELS: Set[str] = {
    # AWSAccount remains the root tenant for normal AWS service resources, while
    # AWSOrganization is a separate top-level tenant for Organizations hierarchy.
    "AWSOrganization",
    # DatabricksWorkspace remains the root tenant for workspace resources, while
    # DatabricksAccount is a separate top-level tenant for the account hierarchy
    # (and is absent on the workspace-only path).
    "DatabricksAccount",
}


def test_sub_resource_relationship():
    """Test that all root nodes have a sub_resource_relationship with rel_label 'RESOURCE' and direction 'INWARD'."""
    errors: List[str] = []
    # Track per-module: for each label, whether at least one Schema variant
    # declares a sub_resource_relationship. A label is considered an "anchored"
    # node when any variant scopes it; aliasing/facet schemas without a
    # sub_resource then don't show up as roots.
    label_has_anchor_per_module: Dict[str, Dict[str, bool]] = {}

    for module_name, node in load_models(cartography.models):
        if module_name not in label_has_anchor_per_module:
            label_has_anchor_per_module[module_name] = {}
        if not issubclass(node, CartographyNodeSchema):
            continue
        sub_resource_relationship = getattr(node, "sub_resource_relationship", None)
        if sub_resource_relationship is None or not isinstance(
            sub_resource_relationship, CartographyRelSchema
        ):
            label_has_anchor_per_module[module_name].setdefault(node.label, False)
            continue
        label_has_anchor_per_module[module_name][node.label] = True
        if (
            sub_resource_relationship.rel_label != "RESOURCE"
            and node.label not in SUB_RESOURCE_REL_LABEL_EXCEPTIONS
        ):
            errors.append(
                f"Node {node.label}: sub_resource_relationship.rel_label is "
                f"'{sub_resource_relationship.rel_label}', expected 'RESOURCE'."
            )
        if sub_resource_relationship.direction != LinkDirection.INWARD:
            errors.append(
                f"Node {node.label}: sub_resource_relationship.direction is "
                f"{sub_resource_relationship.direction}, expected LinkDirection.INWARD."
            )

    for module_name, label_anchors in label_has_anchor_per_module.items():
        if module_name in MODULES_WITHOUT_TENANT_ROOT:
            continue
        unanchored_labels = sorted(
            label
            for label, anchored in label_anchors.items()
            if not anchored
            and label not in GLOBAL_NODE_LABELS
            and label not in ADDITIONAL_TOP_LEVEL_TENANT_LABELS
        )
        if len(unanchored_labels) > 1:
            errors.append(
                f"Module {module_name} has multiple root nodes: "
                f"{', '.join(unanchored_labels)}. Please check the module."
            )

    assert not errors, "sub_resource_relationship violations:\n  - " + "\n  - ".join(
        errors
    )


def test_matchlink_sub_resource_requires_kwargs_matcher():
    with pytest.raises(
        ValueError,
        match="MatchLinkSubResource target_node_matcher PropertyRefs must have set_in_kwargs=True",
    ):
        MatchLinkSubResource(
            target_node_label="AWSAccount",
            target_node_matcher=make_target_node_matcher(
                {"id": PropertyRef("account_id")},
            ),
            direction=LinkDirection.INWARD,
            rel_label="RESOURCE",
        )
