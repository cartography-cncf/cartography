from datetime import datetime

from dateutil.tz import tzutc
from scaleway.autoscaling.v1alpha1 import Capacity
from scaleway.autoscaling.v1alpha1 import InstanceGroup
from scaleway.autoscaling.v1alpha1 import InstancePolicy
from scaleway.autoscaling.v1alpha1 import InstancePolicyAction
from scaleway.autoscaling.v1alpha1 import InstancePolicyType
from scaleway.autoscaling.v1alpha1 import InstanceTemplate
from scaleway.autoscaling.v1alpha1 import InstanceTemplateStatus
from scaleway.autoscaling.v1alpha1 import Loadbalancer
from scaleway.autoscaling.v1alpha1 import Metric
from scaleway.autoscaling.v1alpha1 import MetricAggregate
from scaleway.autoscaling.v1alpha1 import MetricManagedMetric
from scaleway.autoscaling.v1alpha1 import MetricOperator

TEST_ORG_ID = "0681c477-fbb9-4820-b8d6-0eef10cfcd6d"
TEST_PROJECT_ID = "0681c477-fbb9-4820-b8d6-0eef10cfcd6d"
TEST_INSTANCE_TEMPLATE_ID = "11111111-1111-4820-b8d6-0eef10cfcd6d"
TEST_INSTANCE_GROUP_ID = "22222222-2222-4820-b8d6-0eef10cfcd6d"
TEST_SCALING_POLICY_ID = "33333333-3333-4820-b8d6-0eef10cfcd6d"
TEST_PRIVATE_NETWORK_ID = "44444444-4444-4820-b8d6-0eef10cfcd6d"
TEST_LB_ID = "55555555-5555-4820-b8d6-0eef10cfcd6d"
TEST_BACKEND_ID = "66666666-6666-4820-b8d6-0eef10cfcd6d"

SCALEWAY_INSTANCE_TEMPLATES = [
    InstanceTemplate(
        id=TEST_INSTANCE_TEMPLATE_ID,
        commercial_type="DEV1-S",
        volumes={},
        tags=["demo"],
        project_id=TEST_PROJECT_ID,
        name="demo-template",
        private_network_ids=[TEST_PRIVATE_NETWORK_ID],
        status=InstanceTemplateStatus.READY,
        zone="fr-par-1",
        image_id="ubuntu-noble",
        security_group_id=None,
        placement_group_id=None,
        public_ips_v4_count=1,
        public_ips_v6_count=0,
        cloud_init=None,
        created_at=datetime(2025, 3, 20, 14, 49, 48, 107731, tzinfo=tzutc()),
        updated_at=datetime(2025, 3, 20, 14, 49, 48, 107731, tzinfo=tzutc()),
    )
]

SCALEWAY_INSTANCE_GROUPS = [
    InstanceGroup(
        id=TEST_INSTANCE_GROUP_ID,
        project_id=TEST_PROJECT_ID,
        name="demo-group",
        tags=["demo"],
        instance_template_id=TEST_INSTANCE_TEMPLATE_ID,
        capacity=Capacity(
            max_replicas=5,
            min_replicas=2,
            cooldown_delay="300s",
        ),
        loadbalancer=Loadbalancer(
            id=TEST_LB_ID,
            backend_ids=[TEST_BACKEND_ID],
            private_network_id=TEST_PRIVATE_NETWORK_ID,
        ),
        error_messages=[],
        zone="fr-par-1",
        created_at=datetime(2025, 3, 20, 14, 49, 48, 107731, tzinfo=tzutc()),
        updated_at=datetime(2025, 3, 20, 14, 49, 48, 107731, tzinfo=tzutc()),
    )
]

SCALEWAY_SCALING_POLICIES = [
    InstancePolicy(
        id=TEST_SCALING_POLICY_ID,
        name="scale-up-cpu",
        action=InstancePolicyAction.SCALE_UP,
        type_=InstancePolicyType.FLAT_COUNT,
        value=1,
        priority=1,
        instance_group_id=TEST_INSTANCE_GROUP_ID,
        zone="fr-par-1",
        metric=Metric(
            name="cpu high",
            operator=MetricOperator.OPERATOR_GREATER_THAN,
            aggregate=MetricAggregate.AGGREGATE_AVERAGE,
            sampling_range_min=5,
            threshold=80.0,
            managed_metric=MetricManagedMetric.MANAGED_METRIC_INSTANCE_CPU,
            cockpit_metric_name=None,
        ),
    )
]
