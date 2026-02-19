from cartography.intel.container_arch import ARCH_SOURCE_CLUSTER_HINT
from cartography.intel.container_arch import ARCH_SOURCE_IMAGE_DIGEST_EXACT
from cartography.intel.container_arch import ARCH_SOURCE_IMAGE_REF_HINT
from cartography.intel.container_arch import ARCH_SOURCE_RUNTIME_API_EXACT
from cartography.intel.container_arch import ARCH_SOURCE_TASK_DEFINITION_HINT
from cartography.intel.container_arch import guess_architecture_from_image_ref
from cartography.intel.container_arch import normalize_architecture
from cartography.intel.container_arch import normalize_architecture_with_raw


def test_normalize_architecture_aliases() -> None:
    assert normalize_architecture("x86_64") == "amd64"
    assert normalize_architecture("X86_64") == "amd64"
    assert normalize_architecture("x64") == "amd64"
    assert normalize_architecture("aarch64") == "arm64"
    assert normalize_architecture("arm64/v8") == "arm64"
    assert normalize_architecture("armv7l") == "arm"
    assert normalize_architecture("arm/v7") == "arm"
    assert normalize_architecture("i386") == "386"
    assert normalize_architecture("invalid") == "unknown"
    assert normalize_architecture(None) == "unknown"


def test_normalize_architecture_with_raw() -> None:
    assert normalize_architecture_with_raw("x86_64") == ("amd64", "x86_64")
    assert normalize_architecture_with_raw(None) == ("unknown", None)


def test_guess_architecture_from_image_ref() -> None:
    assert guess_architecture_from_image_ref("repo/app:linux-amd64") == "amd64"
    assert guess_architecture_from_image_ref("repo/app:arm64-v8") == "arm64"
    assert guess_architecture_from_image_ref("repo/app:linux/arm/v7") == "arm"
    assert guess_architecture_from_image_ref("repo/app:latest") == "unknown"


def test_architecture_source_constants() -> None:
    assert ARCH_SOURCE_RUNTIME_API_EXACT == "runtime_api_exact"
    assert ARCH_SOURCE_IMAGE_DIGEST_EXACT == "image_digest_exact"
    assert ARCH_SOURCE_TASK_DEFINITION_HINT == "task_definition_hint"
    assert ARCH_SOURCE_CLUSTER_HINT == "cluster_hint"
    assert ARCH_SOURCE_IMAGE_REF_HINT == "image_ref_hint"
