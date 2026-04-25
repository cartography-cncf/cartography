import pytest
from google.api_core.exceptions import GoogleAPICallError

from cartography.intel.gcp.vertex.utils import list_vertex_ai_resources_for_location


def test_list_vertex_ai_resources_for_location_reraises_google_api_call_errors():
    with pytest.raises(GoogleAPICallError):
        list_vertex_ai_resources_for_location(
            fetcher=lambda: (_ for _ in ()).throw(GoogleAPICallError("boom")),
            resource_type="models",
            location="us-central1",
            project_id="test-project",
        )
