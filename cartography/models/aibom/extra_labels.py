from cartography.models.core.nodes import ExtraNodeLabel
from cartography.models.core.nodes import LabelKind

# An AIBOM model component is a reference to a model found while scanning an
# artifact, not a model resource that exists in a provider account. It carried
# `AIModel` before `AIModelReference` existed, which put it in the same label as
# the Bedrock, Vertex, and SageMaker resources and made a count of `AIModel`
# mean nothing. The alias keeps existing queries working until removal.
LEGACY_AI_MODEL = ExtraNodeLabel(
    label="AIModel",
    description="Compatibility label for AIBOM model components, superseded by `AIModelReference`.",
    kind=LabelKind.COMPATIBILITY,
    replacement_label="AIModelReference",
    remove_in="1.0.0",
)
