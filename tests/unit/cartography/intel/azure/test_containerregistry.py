from unittest.mock import Mock
from unittest.mock import patch

import pytest

from cartography.intel.azure.containerregistry import get_client
from cartography.intel.azure.containerregistry import get_image_list
from cartography.intel.azure.containerregistry import get_registry_list
from cartography.intel.azure.containerregistry import get_repository_list
from cartography.intel.azure.containerregistry import load_images
from cartography.intel.azure.containerregistry import load_registries
from cartography.intel.azure.containerregistry import load_repositories
from cartography.intel.azure.containerregistry import sync
from tests.data.azure.containerregistry import CONTAINER_IMAGES
from tests.data.azure.containerregistry import CONTAINER_REGISTRIES
from tests.data.azure.containerregistry import CONTAINER_REPOSITORIES


class TestContainerRegistrySync:

    @patch('cartography.intel.azure.containerregistry.get_client')
    def test_get_registry_list(self, mock_get_client):
        mock_client = Mock()
        mock_get_client.return_value = mock_client
        mock_client.registries.list.return_value = CONTAINER_REGISTRIES

        credentials = Mock()
        subscription_id = 'sub-123'
        regions = ['eastus', 'westus2']
        common_job_parameters = {}

        result = get_registry_list(credentials, subscription_id, regions, common_job_parameters)

        assert len(result) == 2
        assert result[0]['name'] == 'myregistry'
        assert result[0]['location'] == 'eastus'
        assert result[0]['login_server'] == 'myregistry.azurecr.io'
        assert result[0]['sku_name'] == 'Premium'
        assert result[0]['sku_tier'] == 'Premium'
        assert result[0]['admin_user_enabled'] is True
        assert result[0]['tags'] == {'Environment': 'Production', 'Team': 'DevOps'}

        assert result[1]['name'] == 'testregistry'
        assert result[1]['location'] == 'westus2'
        assert result[1]['admin_user_enabled'] is False
        assert result[1]['tags'] == {'Environment': 'Test'}

    @patch('cartography.intel.azure.containerregistry.get_client')
    def test_get_repository_list(self, mock_get_client):
        mock_client = Mock()
        mock_get_client.return_value = mock_client
        mock_client.repositories.list.return_value = CONTAINER_REPOSITORIES

        credentials = Mock()
        subscription_id = 'sub-123'
        registry_name = 'myregistry'
        resource_group = 'rg-acr'
        common_job_parameters = {}

        result = get_repository_list(credentials, subscription_id, registry_name, resource_group, common_job_parameters)

        assert len(result) == 2
        assert result[0]['name'] == 'webapp'
        assert result[0]['registry_name'] == 'myregistry'
        assert result[0]['manifest_count'] == 25
        assert result[0]['tag_count'] == 15
        assert result[0]['size'] == 1073741824

        assert result[1]['name'] == 'api-service'
        assert result[1]['manifest_count'] == 12
        assert result[1]['tag_count'] == 8

    @patch('cartography.intel.azure.containerregistry.get_client')
    def test_get_image_list(self, mock_get_client):
        mock_client = Mock()
        mock_get_client.return_value = mock_client
        mock_client.manifests.list.return_value = CONTAINER_IMAGES

        credentials = Mock()
        subscription_id = 'sub-123'
        registry_name = 'myregistry'
        resource_group = 'rg-acr'
        repository_name = 'webapp'
        common_job_parameters = {}

        result = get_image_list(credentials, subscription_id, registry_name, resource_group, repository_name, common_job_parameters)

        assert len(result) == 2
        assert result[0]['digest'] == 'sha256:abc123def456'
        assert result[0]['repository_name'] == 'webapp'
        assert result[0]['registry_name'] == 'myregistry'
        assert result[0]['architecture'] == 'amd64'
        assert result[0]['os'] == 'linux'
        assert result[0]['tags'] == ['latest', 'v1.2.3', 'stable']

        assert result[1]['digest'] == 'sha256:def456ghi789'
        assert result[1]['architecture'] == 'arm64'
        assert result[1]['tags'] == ['v1.2.2', 'previous']

    def test_load_registries(self):
        session = Mock()
        subscription_id = 'sub-123'
        data_list = [
            {
                'id': '/subscriptions/sub-123/resourceGroups/rg-acr/providers/Microsoft.ContainerRegistry/registries/myregistry',
                'name': 'myregistry',
                'location': 'eastus',
                'login_server': 'myregistry.azurecr.io',
            },
        ]
        update_tag = 12345

        load_registries(session, subscription_id, data_list, update_tag)

        session.execute_write.assert_called_once()

    def test_load_repositories(self):
        session = Mock()
        registry_id = '/subscriptions/sub-123/resourceGroups/rg-acr/providers/Microsoft.ContainerRegistry/registries/myregistry'
        data_list = [
            {
                'name': 'webapp',
                'registry_name': 'myregistry',
                'manifest_count': 25,
            },
        ]
        update_tag = 12345

        load_repositories(session, registry_id, data_list, update_tag)

        session.execute_write.assert_called_once()

    def test_load_images(self):
        session = Mock()
        repository_name = 'webapp'
        registry_name = 'myregistry'
        data_list = [
            {
                'digest': 'sha256:abc123def456',
                'repository_name': 'webapp',
                'registry_name': 'myregistry',
            },
        ]
        update_tag = 12345

        load_images(session, repository_name, registry_name, data_list, update_tag)

        session.execute_write.assert_called_once()

    @patch('cartography.intel.azure.containerregistry.cleanup_container_images')
    @patch('cartography.intel.azure.containerregistry.cleanup_container_repositories')
    @patch('cartography.intel.azure.containerregistry.cleanup_container_registries')
    @patch('cartography.intel.azure.containerregistry.load_images')
    @patch('cartography.intel.azure.containerregistry.load_repositories')
    @patch('cartography.intel.azure.containerregistry.load_registries')
    @patch('cartography.intel.azure.containerregistry.get_image_list')
    @patch('cartography.intel.azure.containerregistry.get_repository_list')
    @patch('cartography.intel.azure.containerregistry.get_registry_list')
    def test_sync(
        self, mock_get_registry_list, mock_get_repository_list, mock_get_image_list,
        mock_load_registries, mock_load_repositories, mock_load_images,
        mock_cleanup_registries, mock_cleanup_repositories, mock_cleanup_images,
    ):

        mock_registries = [
            {
                'id': '/subscriptions/sub-123/resourceGroups/rg-acr/providers/Microsoft.ContainerRegistry/registries/myregistry',
                'name': 'myregistry',
                'resource_group': 'rg-acr',
            },
        ]
        mock_repositories = [
            {
                'name': 'webapp',
                'registry_name': 'myregistry',
            },
        ]
        mock_images = [
            {
                'digest': 'sha256:abc123def456',
                'repository_name': 'webapp',
                'registry_name': 'myregistry',
            },
        ]

        mock_get_registry_list.return_value = mock_registries
        mock_get_repository_list.return_value = mock_repositories
        mock_get_image_list.return_value = mock_images

        session = Mock()
        credentials = Mock()
        subscription_id = 'sub-123'
        update_tag = 12345
        common_job_parameters = {}
        regions = ['eastus']

        sync(session, credentials, subscription_id, update_tag, common_job_parameters, regions)

        mock_get_registry_list.assert_called_once_with(credentials, subscription_id, regions, common_job_parameters)
        mock_load_registries.assert_called_once_with(session, subscription_id, mock_registries, update_tag)

        mock_get_repository_list.assert_called_once_with(credentials, subscription_id, 'myregistry', 'rg-acr', common_job_parameters)
        mock_load_repositories.assert_called_once_with(session, mock_registries[0]['id'], mock_repositories, update_tag)

        mock_get_image_list.assert_called_once_with(credentials, subscription_id, 'myregistry', 'rg-acr', 'webapp', common_job_parameters)
        mock_load_images.assert_called_once_with(session, 'webapp', 'myregistry', mock_images, update_tag)

        mock_cleanup_registries.assert_called_once_with(session, common_job_parameters)
        mock_cleanup_repositories.assert_called_once_with(session, common_job_parameters)
        mock_cleanup_images.assert_called_once_with(session, common_job_parameters)
