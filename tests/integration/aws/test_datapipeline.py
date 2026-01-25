"""
Simplified integration tests for AWS Data Pipeline intel module
"""
import pytest
from unittest.mock import Mock
import sys
import os

# Add the path to import the test data
sys.path.append(os.path.join(os.path.dirname(__file__), '../../data/aws'))
from datapipeline import DESCRIBE_PIPELINES, LIST_PIPELINES


class TestDataPipelineIntegrationSimple:
    """Simplified integration tests for Data Pipeline without Neo4j dependencies"""
    
    def test_data_processing_workflow(self):
        """Test the complete data processing workflow"""
        # Simulate the workflow: list_pipelines -> describe_pipeline -> extract_data
        
        # Step 1: List pipelines (mock response)
        pipeline_list = LIST_PIPELINES
        assert len(pipeline_list) == 2
        
        # Step 2: Get detailed descriptions for each pipeline
        detailed_pipelines = []
        for pipeline_info in pipeline_list:
            # Find matching detailed description
            pipeline_id = pipeline_info["id"]
            for detailed in DESCRIBE_PIPELINES:
                if detailed["pipelineDescription"]["pipelineId"] == pipeline_id:
                    detailed_pipelines.append(detailed)
                    break
        
        assert len(detailed_pipelines) == 2
        
        # Step 3: Extract data like the intel module does
        extracted_pipelines = []
        for pipeline_data in detailed_pipelines:
            pipeline_description = pipeline_data.get("pipelineDescription", {})
            fields = pipeline_description.get("fields", [])
            
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
            
            extracted_pipelines.append(pipeline_info)
        
        # Step 4: Validate extracted data
        assert len(extracted_pipelines) == 2
        
        # Check first pipeline
        pipeline1 = extracted_pipelines[0]
        assert pipeline1["id"] == "df-1234567890ABCDEFGHI"
        assert pipeline1["name"] == "MyDataPipeline"
        assert pipeline1["state"] == "ACTIVE"
        
        # Check second pipeline
        pipeline2 = extracted_pipelines[1]
        assert pipeline2["id"] == "df-0987654321JKLMNOPQR"
        assert pipeline2["name"] == "ETLPipeline"
        assert pipeline2["state"] == "PENDING"
    
    def test_error_handling_workflow(self):
        """Test error handling in the workflow"""
        # Test with missing pipeline in detailed descriptions
        incomplete_pipeline_list = [{"id": "df-missing-pipeline", "name": "MissingPipeline"}]
        
        # Should handle gracefully when detailed description is missing
        detailed_pipelines = []
        for pipeline_info in incomplete_pipeline_list:
            pipeline_id = pipeline_info["id"]
            found = False
            for detailed in DESCRIBE_PIPELINES:
                if detailed["pipelineDescription"]["pipelineId"] == pipeline_id:
                    detailed_pipelines.append(detailed)
                    found = True
                    break
            if not found:
                # Handle missing pipeline gracefully
                print(f"Warning: Pipeline {pipeline_id} not found in detailed descriptions")
        
        # Should have 0 pipelines since none were found
        assert len(detailed_pipelines) == 0
    
    def test_data_validation(self):
        """Test data validation and edge cases"""
        # Test with empty fields
        for pipeline_data in DESCRIBE_PIPELINES:
            pipeline_description = pipeline_data.get("pipelineDescription", {})
            fields = pipeline_description.get("fields", [])
            
            # Extract fields
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
            
            # Validate required fields
            assert pipeline_info["id"] is not None
            assert pipeline_info["id"] != ""
            assert pipeline_info["name"] != ""
            assert pipeline_info["state"] != ""
            assert pipeline_info["userId"] != ""
    
    def test_permission_analysis_simulation(self):
        """Test simulation of permission analysis"""
        # Simulate principals with different permission sets
        principals = [
            {
                "arn": "arn:aws:iam::123456789012:user/admin-user",
                "permissions": ["iam:PassRole", "datapipeline:CreatePipeline", "datapipeline:PutPipelineDefinition", "datapipeline:ActivatePipeline"]
            },
            {
                "arn": "arn:aws:iam::123456789012:user/limited-user", 
                "permissions": ["iam:PassRole", "datapipeline:CreatePipeline"]  # Missing some permissions
            }
        ]
        
        # Required permissions for CAN_EXEC relationship
        required_permissions = ["iam:PassRole", "datapipeline:CreatePipeline", "datapipeline:PutPipelineDefinition", "datapipeline:ActivatePipeline"]
        
        # Analyze which principals have all required permissions
        high_risk_principals = []
        for principal in principals:
            if all(perm in principal["permissions"] for perm in required_permissions):
                high_risk_principals.append(principal["arn"])
        
        # Should only find the admin user
        assert len(high_risk_principals) == 1
        assert "admin-user" in high_risk_principals[0]
        assert "limited-user" not in high_risk_principals[0]


if __name__ == "__main__":
    pytest.main([__file__])
