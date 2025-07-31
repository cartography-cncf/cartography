from unittest.mock import Mock, MagicMock, patch, call, ANY
from googleapiclient.discovery import HttpError
from cartography.intel.gcp import crm
from tests.data.gcp.crm import (
    GCP_ORGANIZATIONS,
    GCP_FOLDERS,
    GCP_PROJECTS,
    GCP_PROJECTS_WITHOUT_PARENT
)


def test_get_gcp_organizations_success():
    """Test successful retrieval of GCP organizations."""
    mock_crm_v1 = Mock()
    mock_request = Mock()
    mock_request.execute.return_value = {"organizations": GCP_ORGANIZATIONS}
    mock_crm_v1.organizations.return_value.search.return_value = mock_request
    result = crm.get_gcp_organizations(mock_crm_v1)
    
    # Assertions
    assert result == GCP_ORGANIZATIONS
    mock_crm_v1.organizations.return_value.search.assert_called_once_with(body={})
    mock_request.execute.assert_called_once()


def test_get_gcp_organizations_http_error():
    """Test handling of HttpError in get_gcp_organizations."""
    mock_crm_v1 = Mock()
    # Mock HttpError
    mock_request = Mock()
    mock_request.execute.side_effect = HttpError(
        resp=Mock(status=403), 
        content=b'{"error": {"message": "Forbidden"}}'
    )
    mock_crm_v1.organizations.return_value.search.return_value = mock_request
    
    # Call the function
    result = crm.get_gcp_organizations(mock_crm_v1)
    
    # Assertions
    assert result == []


def test_get_gcp_organizations_no_organizations_key():
    """Test when API response doesn't contain organizations key."""
    mock_crm_v1 = Mock()
    mock_request = Mock()
    mock_request.execute.return_value = {}
    mock_crm_v1.organizations.return_value.search.return_value = mock_request
    
    result = crm.get_gcp_organizations(mock_crm_v1)
    
    assert result == []


def test_get_gcp_folders_success():
    """Test successful retrieval of GCP folders."""
    mock_crm_v2 = Mock()
    mock_request = Mock()
    mock_request.execute.return_value = {"folders": GCP_FOLDERS}
    mock_crm_v2.folders.return_value.search.return_value = mock_request
    
    result = crm.get_gcp_folders(mock_crm_v2)
    
    assert result == GCP_FOLDERS
    mock_crm_v2.folders.return_value.search.assert_called_once_with(body={})


def test_get_gcp_folders_http_error():
    """Test handling of HttpError in get_gcp_folders."""
    mock_crm_v2 = Mock()
    mock_request = Mock()
    mock_request.execute.side_effect = HttpError(
        resp=Mock(status=403), 
        content=b'{"error": {"message": "Forbidden"}}'
    )
    mock_crm_v2.folders.return_value.search.return_value = mock_request
    
    result = crm.get_gcp_folders(mock_crm_v2)
    
    assert result == []


def test_get_gcp_projects_success():
    """Test successful retrieval of GCP projects with pagination."""
    mock_crm_v1 = Mock()
    mock_request1 = Mock()
    mock_request1.execute.return_value = {"projects": GCP_PROJECTS}

    mock_request2 = Mock()
    mock_request2.execute.return_value = {"projects": GCP_PROJECTS_WITHOUT_PARENT}
    
    # Setup pagination mocks
    mock_crm_v1.projects.return_value.list.return_value = mock_request1
    mock_crm_v1.projects.return_value.list_next.side_effect = [mock_request2, None]
    
    result = crm.get_gcp_projects(mock_crm_v1)
    
    expected = GCP_PROJECTS + GCP_PROJECTS_WITHOUT_PARENT
    assert result == expected
    mock_crm_v1.projects.return_value.list.assert_called_once_with(filter="lifecycleState:ACTIVE")


def test_get_gcp_projects_http_error():
    """Test handling of HttpError in get_gcp_projects."""
    mock_crm_v1 = Mock()
    mock_request = Mock()
    mock_request.execute.side_effect = HttpError(
        resp=Mock(status=403), 
        content=b'{"error": {"message": "Forbidden"}}'
    )
    mock_crm_v1.projects.return_value.list.return_value = mock_request
    
    result = crm.get_gcp_projects(mock_crm_v1)
    
    assert result == []


def test_load_gcp_organizations():
    """Test loading GCP organizations into Neo4j."""
    mock_neo4j_session = Mock()
    gcp_update_tag = 1234567890
    
    crm.load_gcp_organizations(mock_neo4j_session, GCP_ORGANIZATIONS, gcp_update_tag)
    
    expected_calls = []
    for org in GCP_ORGANIZATIONS:
        expected_calls.append(call(
            ANY,  
            OrgName=org["name"],
            DisplayName=org.get("displayName", None),
            LifecycleState=org.get("lifecycleState", None),
            gcp_update_tag=gcp_update_tag
        ))
    
    mock_neo4j_session.run.assert_has_calls(expected_calls)
    assert mock_neo4j_session.run.call_count == len(GCP_ORGANIZATIONS)


def test_load_gcp_folders_with_organization_parent():
    """Test loading GCP folders with organization parent."""
    mock_neo4j_session = Mock()
    gcp_update_tag = 1234567890
    
    crm.load_gcp_folders(mock_neo4j_session, GCP_FOLDERS, gcp_update_tag)
    
    assert mock_neo4j_session.run.call_count == len(GCP_FOLDERS)
    
    call_args = mock_neo4j_session.run.call_args_list[0]
    args, kwargs = call_args
    
    
    folder = GCP_FOLDERS[0]
    assert kwargs['ParentId'] == folder['parent']
    assert kwargs['FolderName'] == folder['name']
    assert kwargs['DisplayName'] == folder.get('displayName', None)
    assert kwargs['LifecycleState'] == folder.get('lifecycleState', None)
    assert kwargs['gcp_update_tag'] == gcp_update_tag


def test_load_gcp_folders_with_folder_parent():
    """Test loading GCP folders with another folder as parent."""
    mock_neo4j_session = Mock()
    gcp_update_tag = 1234567890
    
    folder_with_folder_parent = [{
        "name": "folders/child-1414",
        "parent": "folders/1414",
        "displayName": "child-folder",
        "lifecycleState": "ACTIVE",
        "createTime": "2019-04-11T13:33:07.766Z",
    }]
    
    crm.load_gcp_folders(mock_neo4j_session, folder_with_folder_parent, gcp_update_tag)
    
    assert mock_neo4j_session.run.call_count == 1


def test_load_gcp_projects():
    """Test loading GCP projects into Neo4j."""
    mock_neo4j_session = Mock()
    gcp_update_tag = 1234567890
    
    with patch.object(crm, '_attach_gcp_project_parent') as mock_attach:
        crm.load_gcp_projects(mock_neo4j_session, GCP_PROJECTS, gcp_update_tag)
        
        assert mock_neo4j_session.run.call_count == len(GCP_PROJECTS)
        
        projects_with_parents = [p for p in GCP_PROJECTS if p.get("parent")]
        assert mock_attach.call_count == len(projects_with_parents)


def test_load_gcp_projects_without_parent():
    """Test loading GCP projects without parents."""
    mock_neo4j_session = Mock()
    gcp_update_tag = 1234567890
    
    with patch.object(crm, '_attach_gcp_project_parent') as mock_attach:
        crm.load_gcp_projects(mock_neo4j_session, GCP_PROJECTS_WITHOUT_PARENT, gcp_update_tag)

        assert mock_neo4j_session.run.call_count == len(GCP_PROJECTS_WITHOUT_PARENT)
        
        mock_attach.assert_not_called()


def test_attach_gcp_project_parent_organization():
    """Test attaching project to organization parent."""
    mock_neo4j_session = Mock()
    gcp_update_tag = 1234567890
    
    project_with_org_parent = {
        "projectId": "test-project",
        "parent": {"id": "1337", "type": "organization"}
    }
    
    crm._attach_gcp_project_parent(
        mock_neo4j_session, 
        project_with_org_parent, 
        gcp_update_tag
    )
    
    mock_neo4j_session.run.assert_called_once()
    
    # Checking the call arguments
    call_args = mock_neo4j_session.run.call_args
    args, kwargs = call_args
    
    assert kwargs['ParentId'] == 'organizations/1337'
    assert kwargs['ProjectId'] == 'test-project'
    assert kwargs['gcp_update_tag'] == gcp_update_tag


def test_attach_gcp_project_parent_folder():
    """Test attaching project to folder parent."""
    mock_neo4j_session = Mock()
    gcp_update_tag = 1234567890
    
    project_with_folder_parent = GCP_PROJECTS[0]  
    
    crm._attach_gcp_project_parent(
        mock_neo4j_session, 
        project_with_folder_parent, 
        gcp_update_tag
    )
    
    mock_neo4j_session.run.assert_called_once()
    
    call_args = mock_neo4j_session.run.call_args
    args, kwargs = call_args
    
    assert kwargs['ParentId'] == 'folders/1414'
    assert kwargs['ProjectId'] == project_with_folder_parent['projectId']


def test_attach_gcp_project_parent_unsupported_type():
    """Test error handling for unsupported parent types."""
    mock_neo4j_session = Mock()
    gcp_update_tag = 1234567890
    
    project_with_unsupported_parent = {
        "projectId": "test-project",
        "parent": {"id": "1337", "type": "unsupported"}
    }
    
    try:
        crm._attach_gcp_project_parent(
            mock_neo4j_session, 
            project_with_unsupported_parent, 
            gcp_update_tag
        )
        assert False, "Expected NotImplementedError to be raised"
    except NotImplementedError as e:
        assert "unsupported" in str(e)


@patch('cartography.intel.gcp.crm.run_cleanup_job')
def test_cleanup_gcp_organizations(mock_cleanup):
    """Test cleanup of stale GCP organizations."""
    mock_neo4j_session = Mock()
    common_job_parameters = {"UPDATE_TAG": 1234567890}
    
    crm.cleanup_gcp_organizations(mock_neo4j_session, common_job_parameters)
    
    mock_cleanup.assert_called_once_with(
        "gcp_crm_organization_cleanup.json",
        mock_neo4j_session,
        common_job_parameters
    )


@patch('cartography.intel.gcp.crm.run_cleanup_job')
def test_cleanup_gcp_folders(mock_cleanup):
    """Test cleanup of stale GCP folders."""
    mock_neo4j_session = Mock()
    common_job_parameters = {"UPDATE_TAG": 1234567890}
    
    crm.cleanup_gcp_folders(mock_neo4j_session, common_job_parameters)
    
    mock_cleanup.assert_called_once_with(
        "gcp_crm_folder_cleanup.json",
        mock_neo4j_session,
        common_job_parameters
    )


@patch('cartography.intel.gcp.crm.run_cleanup_job')
def test_cleanup_gcp_projects(mock_cleanup):
    """Test cleanup of stale GCP projects."""
    mock_neo4j_session = Mock()
    common_job_parameters = {"UPDATE_TAG": 1234567890}
    
    crm.cleanup_gcp_projects(mock_neo4j_session, common_job_parameters)
    
    mock_cleanup.assert_called_once_with(
        "gcp_crm_project_cleanup.json",
        mock_neo4j_session,
        common_job_parameters
    )


@patch.object(crm, 'cleanup_gcp_organizations')
@patch.object(crm, 'load_gcp_organizations')
@patch.object(crm, 'get_gcp_organizations')
def test_sync_gcp_organizations(mock_get, mock_load, mock_cleanup):
    """Test syncing GCP organizations end-to-end."""
    mock_neo4j_session = Mock()
    mock_crm_v1 = Mock()
    gcp_update_tag = 1234567890
    common_job_parameters = {"UPDATE_TAG": gcp_update_tag}
    
    mock_get.return_value = GCP_ORGANIZATIONS
    
    crm.sync_gcp_organizations(
        mock_neo4j_session,
        mock_crm_v1,
        gcp_update_tag,
        common_job_parameters
    )
    
    mock_get.assert_called_once_with(mock_crm_v1)
    mock_load.assert_called_once_with(mock_neo4j_session, GCP_ORGANIZATIONS, gcp_update_tag)
    mock_cleanup.assert_called_once_with(mock_neo4j_session, common_job_parameters)


@patch.object(crm, 'cleanup_gcp_folders')
@patch.object(crm, 'load_gcp_folders')
@patch.object(crm, 'get_gcp_folders')
def test_sync_gcp_folders(mock_get, mock_load, mock_cleanup):
    """Test syncing GCP folders end-to-end."""
    mock_neo4j_session = Mock()
    mock_crm_v2 = Mock()
    gcp_update_tag = 1234567890
    common_job_parameters = {"UPDATE_TAG": gcp_update_tag}
    
    mock_get.return_value = GCP_FOLDERS
    
    crm.sync_gcp_folders(
        mock_neo4j_session,
        mock_crm_v2,
        gcp_update_tag,
        common_job_parameters
    )
    
    mock_get.assert_called_once_with(mock_crm_v2)
    mock_load.assert_called_once_with(mock_neo4j_session, GCP_FOLDERS, gcp_update_tag)
    mock_cleanup.assert_called_once_with(mock_neo4j_session, common_job_parameters)


@patch.object(crm, 'cleanup_gcp_projects')
@patch.object(crm, 'load_gcp_projects')
def test_sync_gcp_projects(mock_load, mock_cleanup):
    """Test syncing GCP projects end-to-end."""
    mock_neo4j_session = Mock()
    gcp_update_tag = 1234567890
    common_job_parameters = {"UPDATE_TAG": gcp_update_tag}
    
    all_projects = GCP_PROJECTS + GCP_PROJECTS_WITHOUT_PARENT
    
    crm.sync_gcp_projects(
        mock_neo4j_session,
        all_projects,
        gcp_update_tag,
        common_job_parameters
    )
    
    mock_load.assert_called_once_with(mock_neo4j_session, all_projects, gcp_update_tag)
    mock_cleanup.assert_called_once_with(mock_neo4j_session, common_job_parameters)


# For edge case tests
def test_get_gcp_folders_empty_response():
    """Test when folders API returns empty response."""
    mock_crm_v2 = Mock()
    mock_request = Mock()
    mock_request.execute.return_value = {"folders": []}
    mock_crm_v2.folders.return_value.search.return_value = mock_request
    
    result = crm.get_gcp_folders(mock_crm_v2)
    
    assert result == []


def test_get_gcp_projects_single_page():
    """Test projects retrieval with single page (no pagination)."""
    mock_crm_v1 = Mock()
    mock_request = Mock()
    mock_request.execute.return_value = {"projects": GCP_PROJECTS}
    
    mock_crm_v1.projects.return_value.list.return_value = mock_request
    mock_crm_v1.projects.return_value.list_next.return_value = None
    
    result = crm.get_gcp_projects(mock_crm_v1)
    
    assert result == GCP_PROJECTS


def test_load_gcp_organizations_empty_list():
    """Test loading empty organizations list."""
    mock_neo4j_session = Mock()
    gcp_update_tag = 1234567890
    
    crm.load_gcp_organizations(mock_neo4j_session, [], gcp_update_tag)
    
    mock_neo4j_session.run.assert_not_called()


def test_load_gcp_folders_empty_list():
    """Test loading empty folders list."""
    mock_neo4j_session = Mock()
    gcp_update_tag = 1234567890
    
    crm.load_gcp_folders(mock_neo4j_session, [], gcp_update_tag)
    
    mock_neo4j_session.run.assert_not_called()


def test_load_gcp_projects_empty_list():
    """Test loading empty projects list."""
    mock_neo4j_session = Mock()
    gcp_update_tag = 1234567890
    
    crm.load_gcp_projects(mock_neo4j_session, [], gcp_update_tag)
    
    mock_neo4j_session.run.assert_not_called()