import asyncio

import neo4j


class Seed:
    def __init__(self, neo4j_session: neo4j.Session, update_tag: int) -> None:
        # super().__init__("seed")
        self.neo4j_session = neo4j_session
        self.update_tag = update_tag

    def run(self) -> None:
        self.seed()

    def seed(self, *args) -> None:
        # DOC
        raise NotImplementedError("This method should be overridden in subclasses.")


class AsyncSeed:
    def __init__(self, neo4j_session: neo4j.Session, update_tag: int) -> None:
        self.neo4j_session = neo4j_session
        self.update_tag = update_tag

    def run(self) -> None:
        self.loop = asyncio.get_event_loop()
        self.loop.run_until_complete(self.seed())

    async def seed(self, *args) -> None:
        # DOC
        raise NotImplementedError("This method should be overridden in subclasses.")
