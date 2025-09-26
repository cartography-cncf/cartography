"""
MITRE ATT&CK Framework
Security framework based on MITRE ATT&CK tactics and techniques
"""

from cartography.rules.data.facts.aws.ec2.instances import (
    aws_ec2_instance_internet_exposed,
)
from cartography.rules.data.facts.aws.rds.db_instances import aws_rds_public_access
from cartography.rules.data.facts.aws.s3.buckets import aws_s3_public
from cartography.rules.data.facts.azure.storage.accounts import (
    azure_storage_public_blob_access,
)
from cartography.rules.spec.model import Requirement

t1190_exploit_public_facing_application = Requirement(
    id="t1190_exploit_public_facing_application",
    name="T1190 - Exploit Public-Facing Application",
    description="Adversaries may attempt to take advantage of a weakness in an Internet-facing computer or program using software, data, or commands in order to cause unintended or unanticipated behavior.",
    facts=(
        # AWS
        aws_ec2_instance_internet_exposed,
        aws_s3_public,
        aws_rds_public_access,
        # Azure
        azure_storage_public_blob_access,
    ),
    requirement_url="https://attack.mitre.org/techniques/T1190/",
    # TODO: should we have a per-framework class represent the attributes?
    attributes={
        "tactic": "initial_access",
        "technique_id": "T1190",
        "services": ["ec2", "s3", "rds", "azure_storage"],
        "providers": ["AWS", "AZURE"],
    },
)
