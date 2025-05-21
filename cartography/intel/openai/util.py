from typing import Any
from typing import Generator

import requests


def paginated_get(
    api_session: requests.Session,
    url: str,
    timeout: tuple[int, int],
    after: str | None = None,
) -> Generator[dict[str, Any], None, None]:
    # DOC
    params = {"after": after} if after else {}
    req = api_session.get(
        url,
        params=params,
        timeout=timeout,
    )
    req.raise_for_status()
    result = req.json()
    yield from result.get("data", [])
    if result.get("has_more"):
        yield from paginated_get(
            api_session,
            url,
            timeout=timeout,
            after=result.get("last_id"),
        )
