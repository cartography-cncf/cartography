

from typing import Optional, List, Dict, Any
import json
import requests
import webbrowser
from azure.devops.connection import Connection
from azure.devops.exceptions import AzureDevOpsServiceError

#Azure DevOps API Client Module
class AzureDevOpsClient:
    """Client for interacting with Azure DevOps API"""

    def __init__(self, organization_url, credentials):
        """
        Initialize the Azure DevOps API client

        Args:
            organization_url (str): URL of the Azure DevOps organization (e.g., 'https://dev.azure.com/your-organization')
            credentials: Authentication credentials for Azure DevOps API (BasicAuthentication or OAuthTokenAuthentication object)
        """
        self.organization_url = organization_url
        self.credentials = credentials

    def _get_connection(self) -> Connection:
        """
        Get an Azure DevOps API connection using the stored organization URL and credentials.

        Returns:
            Connection: Azure DevOps API connection object
        """
        return Connection(base_url=self.organization_url, creds=self.credentials)


    def _get_core_client(self) -> Any:
        """
        Get an Azure DevOps Core API client

        Returns:
            Any: Azure DevOps API client
        """
        connection = self._get_connection()
        return connection.clients.get_core_client()

    def _get_git_client(self) -> Any:
        """
        Get an Azure DevOps Git client

        Returns:
            Any: Azure DevOps API client
        """
        connection = self._get_connection()
        return connection.clients.get_git_client()

    def _get_service_hooks_client(self) -> Any:
        """
        Get an Azure DevOps Service Hook client

        Returns:
            Any: Azure DevOps API client
        """
        connection = self._get_connection()
        return connection.clients.get_service_hooks_client()

    def _get_extensions_client(self) -> Any:
        """
        Get an Azure DevOps Extensions client

        Returns:
            Any: Azure DevOps API client
        """
        connection = self._get_connection()
        return connection.clients.get_extension_management_client()

    def get_installed_extensions(self) -> List[Any]:
        """
        Get all installed extensions in an organization

        Returns:
            list: List of extension objects
        """

        extensions_client = self._get_extensions_client()

        try:
            extensions = extensions_client.get_installed_extensions()
            return extensions
        except AzureDevOpsServiceError as e:
            print(f"Error retrieving installed extensions: {e}")
            return []

    def uninstall_extension_by_name(self, extension_id: str) -> bool:
        """
        Uninstall an extension by name

        Args:
            extension_id (str): Name of the publisher and extension in format 'publisherName.extensionName'

        Returns:
            bool: True if the extension was uninstalled successfully, False otherwise
        """
        extensions_client = self._get_extensions_client()
        publisher_name, extension_name = extension_id.split('.', 1)

        try:
            extensions_client.uninstall_extension_by_name(publisher_name, extension_name)
            return True
        except AzureDevOpsServiceError as e:
            print(f"Error uninstalling extension {publisher_name}.{extension_name}: {e}")
            return False

    def install_extension_by_name(self, extension_id: str) -> bool:
        """
        Install an extension by name

        Args:
            extension_id (str): Name of the publisher and extension in format 'publisherName.extensionName'

        Returns:
            bool: True if the extension was installed successfully, False otherwise
        """
        extensions_client = self._get_extensions_client()
        publisher_name, extension_name = extension_id.split('.', 1)

        try:
            extensions_client.install_extension_by_name(publisher_name, extension_name)
            return True
        except AzureDevOpsServiceError as e:
            print(f"Error installing extension {publisher_name}.{extension_name}: {e}")
            return False

    def get_projects(self) -> List[Any]:
        """
        Get all projects in the organization.

        Returns:
            List[Any]: List of project objects from the Azure DevOps API
        """
        core_client = self._get_core_client()

        try:
            projects = core_client.get_projects()
            return projects
        except AzureDevOpsServiceError as e:
            print(f"Error retrieving projects: {e}")
            return []

    def get_repositories(self, project_name: str) -> List[Any]:
        """
        Get all repositories in a project.

        Args:
            project_name (str): Name or ID of the project

        Returns:
            List[Any]: List of repository objects from the Azure DevOps API
        """

        git_client = self._get_git_client()

        try:
            repositories = git_client.get_repositories(project_name)
            return repositories
        except AzureDevOpsServiceError as e:
            print(f"Error retrieving repositories for project {project_name}: {e}")
            return []

    def get_service_hooks(self, publisher_id: str = None, event_type: str = None, consumer_id: str = None, consumer_action_id: str = None) -> List[Any]:
        """
        Get all service hooks in an organization with optional filtering

        Args:
            project_name (str, optional): Name of the project to filter by
            publisher_id (str, optional): ID of the publisher to filter by
            event_type (str, optional): Type of event to filter by
            consumer_id (str, optional): ID of the consumer to filter by
            consumer_action_id (str, optional): ID of the consumer action to filter by

        Returns:
            list: List of service hook subscription objects
        """
        service_hooks_client = self._get_service_hooks_client()

        try:
            # Call the list_subscriptions method with optional filters
            service_hooks = service_hooks_client.list_subscriptions(
                publisher_id=publisher_id,
                event_type=event_type,
                consumer_id=consumer_id,
                consumer_action_id=consumer_action_id
            )

            return service_hooks
        except AzureDevOpsServiceError as e:
            print(f"Error retrieving service hooks: {e}")
            return []

    def get_service_hook_publishers(self) -> List[Any]:
        """
        Get all service hook publishers available in Azure DevOps

        Returns:
            list: List of publisher objects
        """
        service_hooks_client = self._get_service_hooks_client()

        try:
            publishers = service_hooks_client.list_publishers()
            return publishers
        except AzureDevOpsServiceError as e:
            print(f"Error retrieving service hook publishers: {e}")
            return []

    def get_service_hook_consumers(self, publisher_id: str = None) -> List[Any]:
        """
        Get all service hook consumers available in Azure DevOps

        Args:
            publisher_id (str, optional): ID of the publisher to filter consumers by

        Returns:
            list: List of consumer objects
        """
        service_hooks_client = self._get_service_hooks_client()

        try:
            consumers = service_hooks_client.list_consumers(publisher_id=publisher_id)
            return consumers
        except AzureDevOpsServiceError as e:
            print(f"Error retrieving service hook consumers: {e}")
            return []

    def create_service_hook(self, subscription: Dict[str, Any]) -> Any:
        """
        Create a new service hook subscription

        Args:
            subscription (Dict[str, Any]): The subscription definition

        Returns:
            Any: The created subscription object
        """
        service_hooks_client = self._get_service_hooks_client()

        try:
            created_subscription = service_hooks_client.create_subscription(subscription)
            return created_subscription
        except AzureDevOpsServiceError as e:
            print(f"Error creating service hook subscription: {e}")
            return None

    def delete_service_hook(self, subscription_id: str) -> bool:
        """
        Delete a service hook subscription

        Args:
            subscription_id (str): ID of the subscription to delete

        Returns:
            bool: True if deletion was successful, False otherwise
        """
        service_hooks_client = self._get_service_hooks_client()

        try:
            service_hooks_client.delete_subscription(subscription_id)
            return True
        except AzureDevOpsServiceError as e:
            print(f"Error deleting service hook subscription {subscription_id}: {e}")
            return False


    def get_branches(self, project_name: str, repository_name: str) -> List[Any]:
        """
        Get all branches in a repository

        Args:
            project_name (str): Name of the project
            repository_name (str): Name of the repository

        Returns:
            list: List of branch objects
        """
        git_client = self._get_git_client()

        try:
            branches = git_client.get_branches(repository_name, project=project_name)
            return branches
        except AzureDevOpsServiceError as e:
            print(f"Error retrieving branches for repository {repository_name} in project {project_name}: {e}")
            return []
