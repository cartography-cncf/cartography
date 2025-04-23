# Inventory Module
from AzureDevOpsClient import AzureDevOpsClient
from AzureDevOpsAuth import AzureDevOpsAuth

class AzureInventory:
    """Class for managing Azure DevOps inventory and resources.

    This class provides a high-level interface for interacting with Azure DevOps resources
    such as projects, repositories, service hooks, and extensions. It handles the conversion
    of Azure DevOps API objects to JSON-serializable dictionaries.
    """

    def __init__(self, token: str, organization_url: str):
        """
        Initialize the Azure DevOps Inventory manager.

        Args:
            token (str): Azure DevOps Personal Access Token (PAT)
            organization_url (str): URL of the Azure DevOps organization (e.g., 'https://dev.azure.com/your-organization')
        """
        credentials = AzureDevOpsAuth.get_pat_credentials(token)
        self.client = AzureDevOpsClient(organization_url, credentials)

    def get_projects(self):
        """
        Get all projects in an organization.

        Returns:
            list: A list of dictionaries containing project information with the following keys:
                - id: The project ID
                - name: The project name
                - description: The project description
                - url: The project URL
                - state: The project state
        """
        projects = self.client.get_projects()

        project_data = []
        for project in projects:
            data = {
                "id": project.id,
                "name": project.name,
                "description": project.description,
                "url": project.url,
                "state": project.state
            }
            project_data.append(data)

        return project_data

    def get_repositories(self, project_name: str):
        """
        Get all repositories in a project.

        Args:
            project_name (str): The name of the project

        Returns:
            list: A list of dictionaries containing repository information with the following keys:
                - id: The repository ID
                - name: The repository name
                - url: The repository URL
                - default_branch: The default branch of the repository
                - size: The size of the repository
                - remote_url: The remote URL of the repository
                - ssh_url: The SSH URL of the repository
                - web_url: The web URL of the repository
        """
        repositories = self.client.get_repositories(project_name)

        repository_data = []
        for repository in repositories:
            repo_info = {
                "id": repository.id,
                "name": repository.name,
                "url": repository.url,
                "default_branch": repository.default_branch,
                "size": repository.size,
                "remote_url": repository.remote_url,
                "ssh_url": repository.ssh_url,
                "web_url": repository.web_url
            }
            repository_data.append(repo_info)

        return repository_data

    def get_all_project_repositories(self):
        """
        Get all repositories in all projects.

        Returns:
            list: A list of dictionaries containing project information with an additional 'repositories' key
                 that contains a list of repositories for each project.
        """
        projects = self.get_projects()
        result = []

        for project in projects:
            project_info = project.copy()
            project_name = project_info["name"]
            repositories = self.get_repositories(project_name)
            project_info["repositories"] = repositories
            result.append(project_info)

        return result


    def get_service_hooks(self, consumer_id: str = None):
        """
        Get all service hooks in the organization, optionally filtered by consumer ID.

        Args:
            consumer_id (str, optional): The ID of the consumer to filter by

        Returns:
            list: A list of dictionaries containing service hook information with the following keys:
                - id: The service hook ID
                - url: The service hook URL
                - publisherId: The publisher ID
                - eventType: The event type
                - consumerId: The consumer ID
                - consumerActionId: The consumer action ID
                - consumerInputs: The consumer inputs
                - publisherInputs: The publisher inputs
                - status: The service hook status
        """
        service_hooks = self.client.get_service_hooks(consumer_id=consumer_id)

        service_hook_data = []
        for hook in service_hooks:
            hook_info = {
                "id": hook.id,
                "url": hook.url,
                "publisherId": hook.publisher_id,
                "eventType": hook.event_type,
                "consumerId": hook.consumer_id,
                "consumerActionId": hook.consumer_action_id,
                "consumerInputs": hook.consumer_inputs,
                "publisherInputs": hook.publisher_inputs,
                "status": hook.status,
            }
            service_hook_data.append(hook_info)

        return service_hook_data

    def delete_service_hook(self, subscription_id: str):
        """
        Delete a service hook subscription.

        Args:
            subscription_id (str): The ID of the service hook subscription to delete

        Returns:
            bool: True if the service hook was deleted successfully, False otherwise
        """
        return self.client.delete_service_hook(subscription_id)

    def create_service_hook(self):
        """
        Create service hook subscriptions for all projects.

        This method creates three types of service hooks for each project:
        1. Pull request updated hook
        2. Pull request created hook
        3. Git push hook

        All hooks are configured to send events to the Cloudanix webhook consumer.

        Returns:
            bool: True if all service hooks were created successfully
        """

        projects = self.get_projects()
        for project in projects:
            project_id = project["id"]
            print(f"Creating service hook for project: {project_id}")

            pull_request_updated_hook = {
                "consumerId": "Adler.cloudanix-code-webhook.consumer",
                "consumerActionId": "performAction",
                "consumerInputs": {
                    "url": "https://3f00-2402-e280-3e48-3cb-d992-542-b56a-1b6.ngrok-free.app/api/echo"
                },
                "eventType": "git.pullrequest.updated",
                "publisherId": "tfs",
                "publisherInputs": {
                    "projectId": project_id
                }
            }
            pull_request_created_hook = {
                "consumerId": "Adler.cloudanix-code-webhook.consumer",
                "consumerActionId": "performAction",
                "consumerInputs": {
                    "url": "https://3f00-2402-e280-3e48-3cb-d992-542-b56a-1b6.ngrok-free.app/api/echo"
                },
                "eventType": "git.pullrequest.created",
                "publisherId": "tfs",
                "publisherInputs": {
                    "projectId": project_id
                }
            }
            git_push_hook = {
                "consumerId": "Adler.cloudanix-code-webhook.consumer",
                "consumerActionId": "performAction",
                "consumerInputs": {
                    "url": "https://3f00-2402-e280-3e48-3cb-d992-542-b56a-1b6.ngrok-free.app/api/echo"
                },
                "eventType": "git.push",
                "publisherId": "tfs",
                "publisherInputs": {
                    "projectId": project_id
                }
            }
            # Create the service hooks and ignore the returned objects
            self.client.create_service_hook(pull_request_updated_hook)
            self.client.create_service_hook(pull_request_created_hook)
            self.client.create_service_hook(git_push_hook)
            print(f"Service hook created for project: {project_id}")

        return True

        # hook_info = {}
        # if service_hook:
        #     hook_info = {
        #         "id": service_hook.id,
        #         "url": service_hook.url,
        #         "publisherId": service_hook.publisher_id,
        #         "eventType": service_hook.event_type,
        #         "consumerId": service_hook.consumer_id,
        #         "consumerActionId": service_hook.consumer_action_id,
        #         "consumerInputs": service_hook.consumer_inputs,
        #         "publisherInputs": service_hook.publisher_inputs,
        #         "status": service_hook.status,
        #     }
        # return hook_info

    def get_extensions(self):
        """
        Get a list of all installed extensions in the organization.

        Returns:
            list: A list of dictionaries containing extension information with the following keys:
                - extensionId: The extension ID
                - extensionName: The extension name
                - publisherName: The publisher name
                - version: The extension version
                - flags: The extension flags
        """
        extensions =  self.client.get_installed_extensions()
        data = []
        for extension in extensions:
            extension_info = {
                "extensionId": extension.extension_id,
                "extensionName": extension.extension_name,
                "publisherName": extension.publisher_name,
                "version": extension.version,
                "flags": extension.flags ,
            }
            data.append(extension_info)
        return data

    def uninstall_extension(self, extension_id: str):
        """Uninstall an extension by name

        Args:
            extension_id (str): Name of the publisher and extension in format 'publisherName.extensionName'

        Returns:
            bool: True if the extension was uninstalled successfully, False otherwise
        """
        return self.client.uninstall_extension_by_name(extension_id)

    def install_extension(self, extension_id: str):
        """Install an extension by name

        Args:
            extension_id (str): Name of the publisher and extension in format 'publisherName.extensionName'

        Returns:
            bool: True if the extension was installed successfully, False otherwise
        """
        return self.client.install_extension_by_name(extension_id)