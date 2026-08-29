from datetime import datetime

from dateutil.tz import tzutc
from scaleway.container.v1beta1 import Container
from scaleway.container.v1beta1 import ContainerHttpOption
from scaleway.container.v1beta1 import ContainerPrivacy
from scaleway.container.v1beta1 import ContainerProtocol
from scaleway.container.v1beta1 import ContainerSandbox
from scaleway.container.v1beta1 import ContainerStatus
from scaleway.container.v1beta1 import Namespace as ContainerNamespace
from scaleway.container.v1beta1 import NamespaceStatus as ContainerNamespaceStatus
from scaleway.function.v1beta1 import Function
from scaleway.function.v1beta1 import FunctionHttpOption
from scaleway.function.v1beta1 import FunctionPrivacy
from scaleway.function.v1beta1 import FunctionSandbox
from scaleway.function.v1beta1 import FunctionStatus
from scaleway.function.v1beta1 import Namespace as FunctionNamespace
from scaleway.function.v1beta1 import NamespaceStatus as FunctionNamespaceStatus
from scaleway.jobs.v1alpha1 import JobDefinition
from scaleway.jobs.v1alpha1.types import CronSchedule

TEST_ORG_ID = "0681c477-fbb9-4820-b8d6-0eef10cfcd6d"
TEST_PROJECT_ID = "0681c477-fbb9-4820-b8d6-0eef10cfcd6d"

TEST_FUNCTION_NAMESPACE_ID = "aaaaaaaa-1111-4820-b8d6-0eef10cfcd6d"
TEST_FUNCTION_ID = "bbbbbbbb-2222-4820-b8d6-0eef10cfcd6d"
TEST_CONTAINER_NAMESPACE_ID = "cccccccc-3333-4820-b8d6-0eef10cfcd6d"
TEST_CONTAINER_ID = "dddddddd-4444-4820-b8d6-0eef10cfcd6d"
TEST_JOB_DEFINITION_ID = "eeeeeeee-5555-4820-b8d6-0eef10cfcd6d"

_TS = datetime(2025, 3, 20, 14, 49, 48, 107731, tzinfo=tzutc())


SCALEWAY_FUNCTION_NAMESPACES = [
    FunctionNamespace(
        id=TEST_FUNCTION_NAMESPACE_ID,
        name="demo-fn-namespace",
        environment_variables={},
        organization_id=TEST_ORG_ID,
        project_id=TEST_PROJECT_ID,
        status=FunctionNamespaceStatus.READY,
        registry_namespace_id="11111111-1111-1111-1111-111111111111",
        registry_endpoint="rg.fr-par.scw.cloud/funcscwdemo",
        secret_environment_variables=[],
        region="fr-par",
        tags=["demo"],
        error_message=None,
        description="Demo function namespace",
        created_at=_TS,
        updated_at=_TS,
        vpc_integration_activated=False,
    )
]


SCALEWAY_FUNCTIONS = [
    Function(
        id=TEST_FUNCTION_ID,
        name="demo-function",
        namespace_id=TEST_FUNCTION_NAMESPACE_ID,
        status=FunctionStatus.READY,
        environment_variables={},
        min_scale=0,
        max_scale=5,
        runtime="python311",
        memory_limit=256,
        cpu_limit=140,
        handler="handler.handle",
        privacy=FunctionPrivacy.PUBLIC,
        domain_name="demo-function.functions.fnc.fr-par.scw.cloud",
        secret_environment_variables=[],
        region="fr-par",
        http_option=FunctionHttpOption.REDIRECTED,
        runtime_message=None,
        sandbox=FunctionSandbox.V2,
        tags=["demo"],
        timeout="300s",
        error_message=None,
        build_message=None,
        description="Demo function",
        created_at=_TS,
        updated_at=_TS,
        ready_at=_TS,
        private_network_id=None,
    )
]


SCALEWAY_CONTAINER_NAMESPACES = [
    ContainerNamespace(
        id=TEST_CONTAINER_NAMESPACE_ID,
        name="demo-container-namespace",
        environment_variables={},
        organization_id=TEST_ORG_ID,
        project_id=TEST_PROJECT_ID,
        status=ContainerNamespaceStatus.READY,
        registry_namespace_id="22222222-2222-2222-2222-222222222222",
        registry_endpoint="rg.fr-par.scw.cloud/contscwdemo",
        secret_environment_variables=[],
        region="fr-par",
        tags=["demo"],
        error_message=None,
        description="Demo container namespace",
        created_at=_TS,
        updated_at=_TS,
        vpc_integration_activated=False,
    )
]


SCALEWAY_CONTAINERS = [
    Container(
        id=TEST_CONTAINER_ID,
        name="demo-container",
        namespace_id=TEST_CONTAINER_NAMESPACE_ID,
        status=ContainerStatus.READY,
        environment_variables={},
        min_scale=0,
        max_scale=5,
        memory_limit=256,
        cpu_limit=140,
        privacy=ContainerPrivacy.PUBLIC,
        registry_image="rg.fr-par.scw.cloud/contscwdemo/demo:latest",
        max_concurrency=50,
        domain_name="demo-container.containers.fnc.fr-par.scw.cloud",
        protocol=ContainerProtocol.HTTP1,
        port=8080,
        secret_environment_variables=[],
        http_option=ContainerHttpOption.REDIRECTED,
        sandbox=ContainerSandbox.V2,
        local_storage_limit=2000,
        region="fr-par",
        tags=["demo"],
        command=[],
        args=[],
        timeout="300s",
        error_message=None,
        description="Demo container",
        scaling_option=None,
        health_check=None,
        created_at=_TS,
        updated_at=_TS,
        ready_at=_TS,
        private_network_id=None,
    )
]


SCALEWAY_JOB_DEFINITIONS = [
    JobDefinition(
        id=TEST_JOB_DEFINITION_ID,
        name="demo-job",
        cpu_limit=140,
        memory_limit=256,
        image_uri="rg.fr-par.scw.cloud/contscwdemo/job:latest",
        command="python job.py",
        project_id=TEST_PROJECT_ID,
        environment_variables={},
        description="Demo job",
        local_storage_capacity=None,
        region="fr-par",
        created_at=_TS,
        updated_at=_TS,
        job_timeout="3600s",
        cron_schedule=CronSchedule(schedule="0 0 * * *", timezone="UTC"),
    )
]
