# DEPRECATED: compatibility shim for legacy Entra imports. Remove in v1.0.0.
from cartography.intel.microsoft import (
    start_microsoft_ingestion as start_entra_ingestion,
)

__all__ = ["start_entra_ingestion"]
