"""
Integration tests for AWS Data Pipeline intel module
"""
import pytest
from unittest.mock import Mock
import sys
import os
from neo4j import GraphDatabase

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


class TestDataPipelineIntegration:
    """Integration tests for Data Pipeline with Neo4j"""

    @pytest.fixture
    def neo4j_driver(self):
        """Neo4j driver for testing"""
        # Use test database or skip if not available
        try:
            driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "password"))
            # Test connection
            with driver.session() as session:
                session.run("RETURN 1")
            yield driver
            driver.close()
        except Exception:
            pytest.skip("Neo4j not available for integration testing")

    @pytest.fixture
    def mock_aws_session(self):
        """Mock AWS session with test data"""
        mock_session = Mock()
        mock_client = Mock()
        mock_session.client.return_value = mock_client
        
        # Mock the paginator
        mock_paginator = Mock()
        mock_client.get_paginator.return_value = mock_paginator
        mock_paginator.paginate.return_value = [
            {"pipelineIdList": LIST_PIPELINES}
        ]
        
        # Mock describe_pipeline for each pipeline
        mock_client.describe_pipeline.side_effect = DESCRIBE_PIPELINES
        
        return mock_session

    def test_load_datapipeline_pipelines_integration(self, neo4j_driver, mock_aws_session):
        """Test loading Data Pipeline data into Neo4j"""
        # Get test data using real implementation
        pipelines = datapipeline_intel.get_datapipeline_pipelines(mock_aws_session, "us-east-1")
        
        # Load into Neo4j
        with neo4j_driver.session() as session:
            # Clear test data
            session.run("MATCH (n:DataPipeline) WHERE n.id STARTS WITH 'df-' DETACH DELETE n")
            
            # Load test data using real implementation
            datapipeline_intel.load_datapipeline_pipelines(
                session, pipelines, "us-east-1", "123456789012", 1234567890
            )
            
            # Verify data was loaded
            result = session.run("MATCH (pipeline:DataPipeline) RETURN count(pipeline) as count")
            count = result.single()["count"]
            assert count == 2
            
            # Verify specific pipeline data
            result = session.run("""
                MATCH (pipeline:DataPipeline) 
                WHERE pipeline.id = $id
                RETURN pipeline.name, pipeline.state, pipeline.region
            """, id="df-1234567890ABCDEFGHI")
            
            record = result.single()
            assert record is not None
            assert record["pipeline.name"] == "MyDataPipeline"
            assert record["pipeline.state"] == "ACTIVE"
            assert record["pipeline.region"] == "us-east-1"

    def test_pipeline_account_relationship(self, neo4j_driver, mock_aws_session):
        """Test that pipelines are properly linked to AWS accounts"""
        pipelines = datapipeline_intel.get_datapipeline_pipelines(mock_aws_session, "us-east-1")
        
        with neo4j_driver.session() as session:
            # Clear and load data
            session.run("MATCH (n:DataPipeline) WHERE n.id STARTS WITH 'df-' DETACH DELETE n")
            session.run("MERGE (acc:AWSAccount {id: '123456789012'})")
            
            datapipeline_intel.load_datapipeline_pipelines(
                session, pipelines, "us-east-1", "123456789012", 1234567890
            )
            
            # Verify relationship exists (correct direction: AWSAccount->DataPipeline)
            result = session.run("""
                MATCH (account:AWSAccount)-[:RESOURCE]->(pipeline:DataPipeline)
                WHERE account.id = $account_id
                RETURN count(pipeline) as count
            """, account_id="123456789012")
            
            count = result.single()["count"]
            assert count == 2

    def test_sync_function_integration(self, neo4j_driver, mock_aws_session):
        """Test the complete sync function"""
        with neo4j_driver.session() as session:
            # Clear test data
            session.run("MATCH (n:DataPipeline) WHERE n.id STARTS WITH 'df-' DETACH DELETE n")
            session.run("MERGE (acc:AWSAccount {id: '123456789012'})")
            
            # Run complete sync using real implementation
            common_job_parameters = {"UPDATE_TAG": 1234567890, "AWS_ID": "123456789012"}
            datapipeline_intel.sync(
                session, mock_aws_session, ["us-east-1"], "123456789012", 1234567890, common_job_parameters
            )
            
            # Verify results
            result = session.run("MATCH (pipeline:DataPipeline) RETURN count(pipeline) as count")
            count = result.single()["count"]
            assert count == 2
            
            # Verify account relationships (correct direction: AWSAccount->DataPipeline)
            result = session.run("""
                MATCH (account:AWSAccount {id: '123456789012'})-[:RESOURCE]->(pipeline:DataPipeline)
                RETURN count(pipeline) as count
            """)
            
            count = result.single()["count"]
            assert count == 2

    def test_real_implementation_data_extraction(self, mock_aws_session):
        """Test that the real implementation extracts data correctly"""
        # Test each pipeline in our test data
        for i, expected_pipeline in enumerate(DESCRIBE_PIPELINES):
            # Mock the describe_pipeline response
            mock_aws_session.client.return_value.describe_pipeline.return_value = expected_pipeline
            
            result = datapipeline_intel.get_datapipeline_describe_pipeline(
                mock_aws_session, "us-east-1", f"df-test-{i}"
            )
            
            # Verify the real implementation matches expected data
            expected_description = expected_pipeline.get("pipelineDescription", {})
            expected_fields = {field["key"]: field.get("stringValue", "") for field in expected_description.get("fields", [])}
            
            assert result["id"] == expected_description.get("pipelineId")
            assert result["name"] == expected_fields.get("name")
            assert result["description"] == expected_fields.get("description")
            assert result["state"] == expected_fields.get("@state")
            assert result["userId"] == expected_fields.get("userId")

    def test_error_handling_integration(self, neo4j_driver):
        """Test error handling in real implementation"""
        mock_session = Mock()
        mock_client = Mock()
        mock_session.client.return_value = mock_client

        # Mock boto3 ClientError
        import botocore.exceptions
        error_response = {'Error': {'Code': 'AccessDenied', 'Message': 'Access Denied'}}
        mock_client.describe_pipeline.side_effect = botocore.exceptions.ClientError(error_response, 'DescribePipeline')

        result = datapipeline_intel.get_datapipeline_describe_pipeline(
            mock_session, "us-east-1", "df-invalid-id"
        )
        
        # Should return empty dict on error (real implementation behavior)
        assert result == {}

    def test_real_implementation_pipelines_list(self, mock_aws_session):
        """Test that the real implementation lists pipelines correctly"""
        # Test successful pipeline listing
        pipelines = datapipeline_intel.get_datapipeline_pipelines(mock_aws_session, "us-east-1")
        
        # Verify the real implementation returns correct data
        assert len(pipelines) == 2
        assert pipelines[0]["id"] == "df-1234567890ABCDEFGHI"
        assert pipelines[1]["id"] == "df-0987654321JKLMNOPQR"
        
        # Verify data structure
        for pipeline in pipelines:
            assert "id" in pipeline
            assert "name" in pipeline
            assert "description" in pipeline
            assert "state" in pipeline
            assert "userId" in pipeline


if __name__ == "__main__":
    pytest.main([__file__])
