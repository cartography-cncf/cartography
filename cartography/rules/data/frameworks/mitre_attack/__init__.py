# MITRE ATT&CK Framework
from cartography.rules.data.frameworks.mitre_attack.requirements.t1098_account_manipulation import (
    t1098,
)
from cartography.rules.data.frameworks.mitre_attack.requirements.t1190_exploit_public_facing_application import (
    t1190,
)
from cartography.rules.spec.model import Framework

mitre_attack_framework = Framework(
    id="MITRE_ATTACK",
    name="MITRE ATT&CK",
    description="Comprehensive security assessment framework based on MITRE ATT&CK tactics and techniques",
    version="1.0",
    requirements=(
        t1098,
        t1190,
    ),
    source_url="https://attack.mitre.org/",
)
