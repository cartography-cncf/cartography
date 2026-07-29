from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import TargetNodeMatcher
from cartography.models.ontology.labels import API_KEY


@dataclass(frozen=True)
class ModalProxyTokenNodeProperties(CartographyNodeProperties):
    # The `wk-` proxy token id. Proxy tokens are a different credential family from API
    # tokens (`ak-`/`as-`) and cannot be interchanged with them.
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    token_id: PropertyRef = PropertyRef("token_id", extra_index=True)
    created_at: PropertyRef = PropertyRef("created_at")
    # An unscoped proxy token authenticates against EVERY proxy-auth-protected web
    # endpoint in the workspace, so this flag is the blast-radius signal. Indexed for that
    # reason.
    scoped: PropertyRef = PropertyRef("scoped", extra_index=True)


@dataclass(frozen=True)
class ModalProxyTokenToWorkspaceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ModalWorkspace)-[:RESOURCE]->(:ModalProxyToken)
class ModalProxyTokenToWorkspaceRel(CartographyRelSchema):
    target_node_label: str = "ModalWorkspace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("WORKSPACE_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ModalProxyTokenToWorkspaceRelProperties = (
        ModalProxyTokenToWorkspaceRelProperties()
    )


@dataclass(frozen=True)
# Modal proxy tokens gate access to web endpoints declared with requires_proxy_auth.
# Cartography can enumerate the tokens but NOT which endpoints require them:
# requires_proxy_auth is write-only in Modal's API.
class ModalProxyTokenSchema(CartographyNodeSchema):
    label: str = "ModalProxyToken"
    properties: ModalProxyTokenNodeProperties = ModalProxyTokenNodeProperties()
    sub_resource_relationship: ModalProxyTokenToWorkspaceRel = (
        ModalProxyTokenToWorkspaceRel()
    )
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([API_KEY])
