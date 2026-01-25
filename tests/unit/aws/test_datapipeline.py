"""
Unit tests for AWS Data Pipeline intel module
"""
import pytest
from unittest.mock import Mock
import sys
import os

# Add the path to import the test data
sys.path.append(os.path.join(os.path.dirname(__file__), '../../data/aws'))
from datapipeline import DESCRIBE_PIPELINES, LIST_PIPELINES

# Add the path to import the intel module
sys.path.append(os.path.join(os.path.dirname(__file__), '../../../cartography'))
import importlib.util

# Import the datapipeline intel module directly
spec = importlib.util.spec_from_file_location(
    "datapipeline_intel",
    os.path.join(os.path.dirname(__file__), '../../../cartography/intel/aws/datapipeline.py')
)
datapipeline_intel = importlib.util.module_from_spec(spec)
spec.loader.exec_module(datapipeline_intel)


class TestDataPipelineIntel:
    """Test the Data Pipeline intel module with mock data"""

    def test_get_datapipeline_describe_pipeline_success(self):
        """Test successful pipeline description parsing"""
        mock_session = Mock()
        mock_client = Mock()
        mock_session.client.return_value = mock_client

        # Mock the describe_pipeline response
        mock_client.describe_pipeline.return_value = DESCRIBE_PIPELINES[0]

        result = datapipeline_intel.get_datapipeline_describe_pipeline(
            mock_session, "us-east-1", "df-1234567890ABCDEFGHI"
        )
        
        # Verify the real implementation extracts data correctly
        assert result["id"] == "df-1234567890ABCDEFGHI"
        assert result["name"] == "MyDataPipeline"
        assert result["description"] == "Test pipeline for data processing"
        assert result["state"] == "ACTIVE"
        assert result["userId"] == "AIDAEXAMPLEUSER123456789"

    def test_get_datapipeline_describe_pipeline_error(self):
        """Test error handling in describe_pipeline"""
        mock_session = Mock()
        mock_client = Mock()
        mock_session.client.return_value = mock_client

        # Mock boto3 ClientError (the real implementation only catches this specific exception)
        import botocore.exceptions
        error_response = {'Error': {'Code': 'AccessDenied', 'Message': 'Access Denied'}}
        mock_client.describe_pipeline.side_effect = botocore.exceptions.ClientError(error_response, 'DescribePipeline')

        result = datapipeline_intel.get_datapipeline_describe_pipeline(
            mock_session, "us-east-1", "df-invalid-id"
        )
        
        # Should return empty dict on error (real implementation behavior)
        assert result == {}

    def test_get_datapipeline_pipelines_success(self):
        """Test successful pipeline listing"""
        mock_session = Mock()
        mock_client = Mock()
        mock_session.client.return_value = mock_client

        # Mock the paginator
        mock_paginator = Mock()
        mock_client.get_paginator.return_value = mock_paginator

        # Mock pagination response
        mock_paginator.paginate.return_value = [
            {"pipelineIdList": LIST_PIPELINES}
        ]
        
        # Mock describe_pipeline for each pipeline
        mock_client.describe_pipeline.side_effect = DESCRIBE_PIPELINES

        result = datapipeline_intel.get_datapipeline_pipelines(
            mock_session, "us-east-1"
        )
        
        # The real implementation returns a list, not None
        assert result is not None
        assert len(result) == 2
        assert result[0]["id"] == "df-1234567890ABCDEFGHI"
        assert result[1]["id"] == "df-0987654321JKLMNOPQR"

    def test_get_datapipeline_pipelines_error(self):
        """Test error handling in pipeline listing"""
        mock_session = Mock()
        mock_client = Mock()
        mock_session.client.return_value = mock_client

        # Mock boto3 ClientError for list_pipelines
        import botocore.exceptions
        error_response = {'Error': {'Code': 'AccessDenied', 'Message': 'Access Denied'}}
        mock_paginator = Mock()
        mock_client.get_paginator.return_value = mock_paginator
        mock_paginator.paginate.side_effect = botocore.exceptions.ClientError(error_response, 'ListPipelines')

        result = datapipeline_intel.get_datapipeline_pipelines(
            mock_session, "us-east-1"
        )
        
        # Should return empty list on error (real implementation behavior)
        assert result == []

    def test_real_implementation_parsing(self):
        """Test that the real implementation parses test data correctly"""
        mock_session = Mock()
        mock_client = Mock()
        mock_session.client.return_value = mock_client

        # Test each pipeline in our test data
        for i, expected_pipeline in enumerate(DESCRIBE_PIPELINES):
            mock_client.describe_pipeline.return_value = expected_pipeline
            
            result = datapipeline_intel.get_datapipeline_describe_pipeline(
                mock_session, "us-east-1", f"df-test-{i}"
            )
            
            # Verify the real implementation matches expected data
            expected_description = expected_pipeline.get("pipelineDescription", {})
            expected_fields = {field["key"]: field.get("stringValue", "") for field in expected_description.get("fields", [])}
            
            assert result["id"] == expected_description.get("pipelineId")
            assert result["name"] == expected_fields.get("name")
            assert result["description"] == expected_fields.get("description")
            assert result["state"] == expected_fields.get("@state")
            assert result["userId"] == expected_fields.get("userId")

    def test_aws_handle_regions_decorator(self):
        """Test that the function has the required @aws_handle_regions decorator"""
        # Check if the function has the decorator (indicates it's wrapped)
        assert hasattr(datapipeline_intel.get_datapipeline_describe_pipeline, '__wrapped__')
        
        # Test that the function is properly decorated by checking it has the wrapper attributes
        func = datapipeline_intel.get_datapipeline_describe_pipeline
        assert hasattr(func, '__wrapped__')  # Indicates it's decorated

    def test_data_extraction_completeness(self):
        """Test that the real implementation extracts all required fields"""
        mock_session = Mock()
        mock_client = Mock()
        mock_session.client.return_value = mock_client

        # Test each pipeline in our test data
        for pipeline_data in DESCRIBE_PIPELINES:
            mock_client.describe_pipeline.return_value = pipeline_data
            
            result = datapipeline_intel.get_datapipeline_describe_pipeline(
                mock_session, "us-east-1", "test-pipeline"
            )
            
            # Verify all required fields are extracted by the real implementation
            assert result["id"] is not None
            assert result["name"] != ""
            assert result["description"] != ""
            assert result["state"] != ""
            assert result["userId"] != ""


if __name__ == "__main__":
    pytest.main([__file__])
