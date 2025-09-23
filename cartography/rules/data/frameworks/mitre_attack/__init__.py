# MITRE ATT&CK Framework
from cartography.rules.data.frameworks.mitre_attack.requirements import (
    t1190_exploit_public_facing_application,
)
from cartography.rules.spec.model import Framework

mitre_attack_framework = Framework(
    id="MITRE_ATTACK",
    name="MITRE ATT&CK",
    description="Comprehensive security assessment framework based on MITRE ATT&CK tactics and techniques",
    version="1.0",
    requirements=(t1190_exploit_public_facing_application,),
    source_url="https://attack.mitre.org/",
)
