import pytest

from tests.sharding import assign_shards
from tests.sharding import parse_shard


def test_assign_shards_covers_every_file_exactly_once_and_balances_load():
    # Arrange
    durations = {"a.py": 50.0, "b.py": 40.0, "c.py": 30.0, "d.py": 20.0, "e.py": 10.0}

    # Act
    assignment = assign_shards(durations, durations, total=2)

    # Assert
    assert set(assignment) == set(durations)
    loads = [0.0, 0.0]
    for path, shard in assignment.items():
        loads[shard] += durations[path]
    assert sorted(loads) == [70.0, 80.0]


def test_assign_shards_is_independent_of_input_order():
    # Arrange
    files = [f"test_{i}.py" for i in range(20)]
    durations = {f: float(i % 7) for i, f in enumerate(files)}

    # Act and assert
    assert assign_shards(files, durations, 4) == assign_shards(
        reversed(files),
        durations,
        4,
    )


def test_assign_shards_weights_unknown_files_as_the_median():
    # Arrange: the median is 6. Weighted as 6, the new file joins `six.py`; weighted
    # as 0 (or any small default) it would join `ten.py` instead.
    durations = {"ten.py": 10.0, "six.py": 6.0, "five.py": 5.0}

    # Act
    assignment = assign_shards([*durations, "new.py"], durations, total=2)

    # Assert
    assert assignment["new.py"] == assignment["six.py"]
    assert assignment["new.py"] != assignment["ten.py"]


@pytest.mark.parametrize(
    "value, expected",
    [("0/1", (0, 1)), ("3/4", (3, 4))],
)
def test_parse_shard(value, expected):
    assert parse_shard(value) == expected


@pytest.mark.parametrize("value", ["", "1", "4/4", "-1/4", "0/0", "a/b"])
def test_parse_shard_rejects_invalid_values(value):
    with pytest.raises(ValueError):
        parse_shard(value)
