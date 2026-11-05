from cartography.rules.data.rules import RULES
from cartography.rules.data.rules.kubernetes_storage_security import (
    kubernetes_containers_using_raw_block_persistent_storage,
)
from cartography.rules.data.rules.kubernetes_storage_security import (
    kubernetes_internet_exposed_containers_with_writable_persistent_storage,
)
from cartography.rules.data.rules.kubernetes_storage_security import (
    KubernetesContainerPersistentStorageFinding,
)
from cartography.rules.spec.model import Maturity
from cartography.rules.spec.model import Module

RULES_UNDER_TEST = (
    kubernetes_internet_exposed_containers_with_writable_persistent_storage,
    kubernetes_containers_using_raw_block_persistent_storage,
)


def test_kubernetes_storage_security_rules_are_registered() -> None:
    for rule in RULES_UNDER_TEST:
        assert RULES[rule.id] is rule


def test_kubernetes_storage_security_rule_shape() -> None:
    for rule in RULES_UNDER_TEST:
        assert rule.output_model is KubernetesContainerPersistentStorageFinding
        assert len(rule.facts) == 1
        assert rule.facts[0].module == Module.KUBERNETES
        assert rule.facts[0].maturity == Maturity.EXPERIMENTAL
        assert rule.facts[0].asset_label == "KubernetesContainer"
        assert rule.facts[0].asset_id_field == "container_id"
        assert rule.facts[0].identity_fields == ("container_id",)
