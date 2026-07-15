from dataclasses import dataclass

from cartography.models.core.nodes import ExtraNodeLabel


@dataclass(frozen=True)
class AIAgentLabel(ExtraNodeLabel):
    """A aibom node participating in the shared AIAgent graph interface."""

    label: str = "AIAgent"


@dataclass(frozen=True)
class AIEmbeddingLabel(ExtraNodeLabel):
    """A aibom node participating in the shared AIEmbedding graph interface."""

    label: str = "AIEmbedding"


@dataclass(frozen=True)
class AIMemoryLabel(ExtraNodeLabel):
    """A aibom node participating in the shared AIMemory graph interface."""

    label: str = "AIMemory"


@dataclass(frozen=True)
class AIPromptLabel(ExtraNodeLabel):
    """A aibom node participating in the shared AIPrompt graph interface."""

    label: str = "AIPrompt"


@dataclass(frozen=True)
class AIToolLabel(ExtraNodeLabel):
    """A aibom node participating in the shared AITool graph interface."""

    label: str = "AITool"
