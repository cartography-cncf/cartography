"""
Framework Registry

Central registry of all available security frameworks for Cartography Rules.
"""

from cartography.rules.data.frameworks.mitre_attack import mitre_attack_framework

# Framework registry - all available frameworks
FRAMEWORKS = {
    "mitre-attack": mitre_attack_framework,
}
