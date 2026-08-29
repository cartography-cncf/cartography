import pytest


@pytest.fixture(autouse=True)
def no_real_sleep(mocker):
    """Never sleep for real in a unit test.

    Several modules wrap API calls in `@backoff.on_exception`, so a unit test that
    exercises a retry path sleeps for the full backoff schedule unless it patches
    `time.sleep` itself. Patching it here keeps that cost out of the suite and stops
    it from creeping back in.

    Tests that patch `time.sleep` themselves (to assert on the delays, say) still
    work: their patch is applied after this one and wins.
    """
    mocker.patch("time.sleep")
