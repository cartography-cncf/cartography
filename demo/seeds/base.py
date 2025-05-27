import asyncio

import neo4j


class Seed:
    """
    Base class for seeding data into Neo4j.
    This class should be subclassed to implement specific seeding logic.
    """

    def __init__(self, neo4j_session: neo4j.Session, update_tag: int) -> None:
        # super().__init__("seed")
        self.neo4j_session = neo4j_session
        self.update_tag = update_tag

    def run(self) -> None:
        """
        Run the seeding process synchronously.
        """
        self.seed()

    def seed(self, *args) -> None:
        """
        Seed the Neo4j database with data.
        This method should be overridden in subclasses to implement specific seeding logic.
        """
        raise NotImplementedError("This method should be overridden in subclasses.")


class AsyncSeed:
    """
    Base class for seeding data into Neo4j asynchronously.
    This class should be subclassed to implement specific asynchronous seeding logic.
    """

    def __init__(self, neo4j_session: neo4j.Session, update_tag: int) -> None:
        self.neo4j_session = neo4j_session
        self.update_tag = update_tag

    def run(self) -> None:
        """
        Run the asynchronous seeding process.
        This method creates an event loop and runs the seed method until completion.
        """
        self.loop = asyncio.get_event_loop()
        self.loop.run_until_complete(self.seed())

    async def seed(self, *args) -> None:
        """
        Seed the Neo4j database with data asynchronously.
        This method should be overridden in subclasses to implement specific asynchronous seeding logic.
        """
        raise NotImplementedError("This method should be overridden in subclasses.")
