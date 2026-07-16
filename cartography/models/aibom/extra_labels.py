from cartography.models.core.nodes import ExtraNodeLabel

AI_AGENT = ExtraNodeLabel(
    label="AIAgent",
    description="A aibom node participating in the shared AIAgent graph interface.",
)


AI_EMBEDDING = ExtraNodeLabel(
    label="AIEmbedding",
    description="A aibom node participating in the shared AIEmbedding graph interface.",
)


AI_MEMORY = ExtraNodeLabel(
    label="AIMemory",
    description="A aibom node participating in the shared AIMemory graph interface.",
)


AI_PROMPT = ExtraNodeLabel(
    label="AIPrompt",
    description="A aibom node participating in the shared AIPrompt graph interface.",
)


AI_TOOL = ExtraNodeLabel(
    label="AITool",
    description="A aibom node participating in the shared AITool graph interface.",
)
