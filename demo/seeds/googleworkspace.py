import cartography.intel.googleworkspace.devices
import cartography.intel.googleworkspace.groups
import cartography.intel.googleworkspace.tenant
import cartography.intel.googleworkspace.users
import tests.data.googleworkspace.api
import tests.data.googleworkspace.devices
import tests.data.googleworkspace.tenant
from demo.seeds.base import Seed


class GoogleWorkspaceSeed(Seed):
    @property
    def common_job_parameters(self) -> dict:
        return {
            "UPDATE_TAG": self.update_tag,
            "CUSTOMER_ID": tests.data.googleworkspace.tenant.GOOGLEWORKSPACE_TENANT_DATA[
                "id"
            ],
        }

    def seed(self, *args) -> None:
        # Seed tenant
        self._seed_tenant()
        # Seed users
        self._seed_users()
        # Seed groups
        self._seed_groups()
        # Seed devices
        self._seed_devices()

    def _seed_tenant(self) -> None:
        cartography.intel.googleworkspace.tenant.load_googleworkspace_tenant(
            self.neo4j_session,
            tests.data.googleworkspace.tenant.GOOGLEWORKSPACE_TENANT_DATA,
            self.update_tag,
        )

    def _seed_users(self) -> None:
        # Transform the users data
        raw_users = cartography.intel.googleworkspace.users.transform_users(
            tests.data.googleworkspace.api.MOCK_GOOGLEWORKSPACE_USERS_RESPONSE
        )

        # Load users
        cartography.intel.googleworkspace.users.load_googleworkspace_users(
            self.neo4j_session,
            raw_users,
            self.update_tag,
            self.common_job_parameters["CUSTOMER_ID"],
        )

        # Cleanup
        cartography.intel.googleworkspace.users.cleanup_googleworkspace_users(
            self.neo4j_session,
            self.common_job_parameters,
        )

    def _seed_groups(self) -> None:
        customer_id = self.common_job_parameters["CUSTOMER_ID"]

        # Transform groups data
        groups, group_member_relationships, group_owner_relationships = (
            cartography.intel.googleworkspace.groups.transform_groups(
                tests.data.googleworkspace.api.MOCK_GOOGLEWORKSPACE_GROUPS_RESPONSE,
                tests.data.googleworkspace.api.MOCK_GOOGLEWORKSPACE_MEMBERS_BY_GROUP_EMAIL,
            )
        )

        # Load groups
        cartography.intel.googleworkspace.groups.load_googleworkspace_groups(
            self.neo4j_session,
            groups,
            customer_id,
            self.update_tag,
        )

        # Load group-to-group relationships
        cartography.intel.googleworkspace.groups.load_googleworkspace_group_to_group_relationships(
            self.neo4j_session,
            group_member_relationships,
            group_owner_relationships,
            customer_id,
            self.update_tag,
        )

        # Cleanup
        cartography.intel.googleworkspace.groups.cleanup_googleworkspace_groups(
            self.neo4j_session,
            self.common_job_parameters,
            customer_id,
            self.update_tag,
        )

    def _seed_devices(self) -> None:
        customer_id = self.common_job_parameters["CUSTOMER_ID"]

        # Transform devices data
        transformed_devices = (
            cartography.intel.googleworkspace.devices.transform_devices(
                tests.data.googleworkspace.devices.MOCK_DEVICES_RESPONSE,
                tests.data.googleworkspace.devices.MOCK_DEVICE_USERS_RESPONSE,
            )
        )

        # Load devices
        cartography.intel.googleworkspace.devices.load_devices(
            self.neo4j_session,
            transformed_devices,
            customer_id,
            self.update_tag,
        )

        # Cleanup
        cartography.intel.googleworkspace.devices.cleanup_devices(
            self.neo4j_session,
            self.common_job_parameters,
        )
