import cartography.intel.scaleway.iam.apikeys
import cartography.intel.scaleway.iam.applications
import cartography.intel.scaleway.iam.groups
import cartography.intel.scaleway.iam.users
import cartography.intel.scaleway.instances.instances
import cartography.intel.scaleway.projects
import cartography.intel.scaleway.storage.snapshots
import cartography.intel.scaleway.storage.volumes
import tests.data.scaleway.iam
import tests.data.scaleway.instances
import tests.data.scaleway.projects
import tests.data.scaleway.storages
from demo.seeds.base import Seed

ORG_ID = "0681c477-fbb9-4820-b8d6-0eef10cfcd6d"


class ScalewaySeed(Seed):
    def seed(self, *args) -> None:
        self._seed_projects()
        self._seed_users()
        self._seed_applications()
        self._seed_groups()
        self._seed_apikeys()
        self._seed_volumes()
        self._seed_snapshots()
        self._seed_instances()

    def _seed_projects(self) -> None:
        data = cartography.intel.scaleway.projects.transform_projects(
            tests.data.scaleway.projects.SCALEWAY_PROJECTS
        )
        cartography.intel.scaleway.projects.load_projects(
            self.neo4j_session, data, org_id=ORG_ID, update_tag=self.update_tag
        )

    def _seed_users(self) -> None:
        data = cartography.intel.scaleway.iam.users.transform_users(
            tests.data.scaleway.iam.SCALEWAY_USERS
        )
        cartography.intel.scaleway.iam.users.load_users(
            self.neo4j_session, data, org_id=ORG_ID, update_tag=self.update_tag
        )

    def _seed_applications(self) -> None:
        data = cartography.intel.scaleway.iam.applications.transform_applications(
            tests.data.scaleway.iam.SCALEWAY_APPLICATIONS
        )
        cartography.intel.scaleway.iam.applications.load_applications(
            self.neo4j_session, data, org_id=ORG_ID, update_tag=self.update_tag
        )

    def _seed_groups(self) -> None:
        data = cartography.intel.scaleway.iam.groups.transform_groups(
            tests.data.scaleway.iam.SCALEWAY_GROUPS
        )
        cartography.intel.scaleway.iam.groups.load_groups(
            self.neo4j_session, data, org_id=ORG_ID, update_tag=self.update_tag
        )

    def _seed_apikeys(self) -> None:
        data = cartography.intel.scaleway.iam.apikeys.transform_apikeys(
            tests.data.scaleway.iam.SCALEWAY_APIKEYS
        )
        cartography.intel.scaleway.iam.apikeys.load_apikeys(
            self.neo4j_session, data, org_id=ORG_ID, update_tag=self.update_tag
        )

    def _seed_volumes(self) -> None:
        data = cartography.intel.scaleway.storage.volumes.transform_volumes(
            tests.data.scaleway.storages.SCALEWAY_VOLUMES
        )
        cartography.intel.scaleway.storage.volumes.load_volumes(
            self.neo4j_session, data, update_tag=self.update_tag
        )

    def _seed_snapshots(self) -> None:
        data = cartography.intel.scaleway.storage.snapshots.transform_snapshots(
            tests.data.scaleway.storages.SCALEWAY_SNAPSHOTS
        )
        cartography.intel.scaleway.storage.snapshots.load_snapshots(
            self.neo4j_session, data, update_tag=self.update_tag
        )

    def _seed_instances(self) -> None:
        data = cartography.intel.scaleway.instances.instances.transform_instances(
            tests.data.scaleway.instances.SCALEWAY_INSTANCES
        )
        cartography.intel.scaleway.instances.instances.load_instances(
            self.neo4j_session, data, update_tag=self.update_tag
        )
