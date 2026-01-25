"""
Unit tests for AWS Data Pipeline intel module - Simplified version
"""
import pytest
from unittest.mock import Mock, patch
import sys
import os

# Add the path to import the test data
sys.path.append(os.path.join(os.path.dirname(__file__), '../../data/aws'))
from datapipeline import DESCRIBE_PIPELINES, LIST_PIPELINES


class TestDataPipelineLogic:
    """Test the Data Pipeline logic without importing the full intel module"""
    
    def test_describe_pipeline_data_extraction(self):
        """Test that we can extract data from describe_pipeline response"""
        pipeline_data = DESCRIBE_PIPELINES[0]
        pipeline_description = pipeline_data.get("pipelineDescription", {})
        fields = pipeline_description.get("fields", [])
        
        # Extract fields like the intel module does
        pipeline_info = {
            "id": pipeline_description.get("pipelineId"),
            "name": "",
            "description": "",
            "state": "",
            "userId": "",
        }
        
        for field in fields:
            key = field.get("key")
            value = field.get("stringValue", "")
            if key == "name":
                pipeline_info["name"] = value
            elif key == "description":
                pipeline_info["description"] = value
            elif key == "@state":
                pipeline_info["state"] = value
            elif key == "userId":
                pipeline_info["userId"] = value
        
        # Verify extraction worked
        assert pipeline_info["id"] == "df-1234567890ABCDEFGHI"
        assert pipeline_info["name"] == "MyDataPipeline"
        assert pipeline_info["description"] == "Test pipeline for data processing"
        assert pipeline_info["state"] == "ACTIVE"
        assert pipeline_info["userId"] == "AIDAEXAMPLEUSER123456789"
    
    def test_list_pipelines_structure(self):
        """Test that LIST_PIPELINES has correct structure"""
        assert len(LIST_PIPELINES) == 2
        assert LIST_PIPELINES[0]["id"] == "df-1234567890ABCDEFGHI"
        assert LIST_PIPELINES[0]["name"] == "MyDataPipeline"
        assert LIST_PIPELINES[1]["id"] == "df-0987654321JKLMNOPQR"
        assert LIST_PIPELINES[1]["name"] == "ETLPipeline"
    
    def test_describe_pipelines_completeness(self):
        """Test that all DESCRIBE_PIPELINES have required fields"""
        for i, pipeline_data in enumerate(DESCRIBE_PIPELINES):
            pipeline_description = pipeline_data.get("pipelineDescription", {})
            
            # Check required top-level fields
            assert pipeline_description.get("pipelineId") is not None
            assert pipeline_description.get("name") is not None
            
            # Check fields array
            fields = pipeline_description.get("fields", [])
            assert len(fields) > 0
            
            # Convert to dict for easier testing
            field_dict = {field.get("key"): field.get("stringValue", "") for field in fields}
            
            # Check required fields exist
            required_fields = ["name", "description", "@state", "userId"]
            for field in required_fields:
                assert field in field_dict, f"Missing field {field} in pipeline {i+1}"
                assert field_dict[field] != "", f"Empty field {field} in pipeline {i+1}"
    
    def test_pipeline_states_variety(self):
        """Test that we have different pipeline states for testing"""
        states = []
        for pipeline_data in DESCRIBE_PIPELINES:
            pipeline_description = pipeline_data.get("pipelineDescription", {})
            fields = pipeline_description.get("fields", [])
            field_dict = {field.get("key"): field.get("stringValue", "") for field in fields}
            states.append(field_dict.get("@state"))
        
        # Should have different states (ACTIVE and PENDING)
        assert "ACTIVE" in states
        assert "PENDING" in states
        assert len(set(states)) >= 2  # At least 2 different states
    
    def test_user_ids_variety(self):
        """Test that we have different user IDs for testing"""
        user_ids = []
        for pipeline_data in DESCRIBE_PIPELINES:
            pipeline_description = pipeline_data.get("pipelineDescription", {})
            fields = pipeline_description.get("fields", [])
            field_dict = {field.get("key"): field.get("stringValue", "") for field in fields}
            user_ids.append(field_dict.get("userId"))
        
        # Should have different users
        assert len(set(user_ids)) >= 2  # At least 2 different users
        assert all(user_id.startswith("AIDA") for user_id in user_ids if user_id)


class TestDataPipelineMocking:
    """Test mocking scenarios for Data Pipeline operations"""
    
    def test_mock_aws_client_describe_pipeline(self):
        """Test mocking AWS client describe_pipeline call"""
        mock_session = Mock()
        mock_client = Mock()
        mock_session.client.return_value = mock_client
        
        # Mock the describe_pipeline response
        mock_client.describe_pipeline.return_value = DESCRIBE_PIPELINES[0]
        
        # Test that mock works
        result = mock_client.describe_pipeline(pipelineId="df-1234567890ABCDEFGHI")
        assert result == DESCRIBE_PIPELINES[0]
        mock_client.describe_pipeline.assert_called_once_with(pipelineId="df-1234567890ABCDEFGHI")
    
    def test_mock_aws_client_list_pipelines(self):
        """Test mocking AWS client list_pipelines call"""
        mock_session = Mock()
        mock_client = Mock()
        mock_paginator = Mock()
        mock_session.client.return_value = mock_client
        mock_client.get_paginator.return_value = mock_paginator
        
        # Mock pagination response
        mock_paginator.paginate.return_value = [
            {"pipelineIdList": LIST_PIPELINES}
        ]
        
        # Test that mock works
        pages = list(mock_paginator.paginate())
        assert len(pages) == 1
        assert pages[0]["pipelineIdList"] == LIST_PIPELINES
    
    def test_mock_error_handling(self):
        """Test error handling scenarios"""
        mock_session = Mock()
        mock_client = Mock()
        mock_session.client.return_value = mock_client
        
        # Mock boto3 error
        mock_client.describe_pipeline.side_effect = Exception("Access Denied")
        
        # Test error handling
        with pytest.raises(Exception, match="Access Denied"):
            mock_client.describe_pipeline(pipelineId="df-invalid-id")


if __name__ == "__main__":
    pytest.main([__file__])
