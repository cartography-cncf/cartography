import logging
from typing import Dict
from typing import List
from typing import Set

import pytest

import cartography.models
from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import MatchLinkSubResource
from tests.utils import load_models

logger = logging.getLogger(__name__)


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
    # OIDC providers express a trust relationship with the cluster rather than
    # a strict ownership; an OIDC provider can in principle be referenced by
    # multiple clusters.
    "KubernetesOIDCProvider",
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
    "AWSServicePrincipal",
    "AWSTag",
    # CVE records ingested by CrowdStrike are public CVEs shared across tenants;
    # CrowdstrikeCVESchema sets scoped_cleanup=False explicitly.
    "CrowdstrikeFinding",
    # Public/global registry data.
    "DockerScoutPublicImage",
    "DockerScoutPublicImageTag",
    # GitHub nodes that can exist outside any organization. A GitHubUser may
    # be unaffiliated, and a GitHubRepository can be owned by a personal user
    # rather than an organization, so neither is anchored to a single tenant.
    "GitHubRepository",
    "GitHubUser",
    # Shared GitHub nodes (cross-org / cross-repo).
    "ProgrammingLanguage",
    "PythonLibrary",
    # Workday canonical human (mirrors the ontology pattern).
    "WorkdayHuman",
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
            if not anchored and label not in GLOBAL_NODE_LABELS
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
