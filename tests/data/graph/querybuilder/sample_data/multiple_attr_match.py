MERGE_PERSONS = """
MERGE (s1:Person{id: 1, first_name: "Homer", last_name: "Simpson", lastupdated: 1})
MERGE (s2:Person{id: 2, first_name: "Marge", last_name: "Simpson", lastupdated: 1})
MERGE (s3:Person{id: 3, first_name: "Bart", last_name: "Simpson", lastupdated: 1})
MERGE (s4:Person{id: 4, first_name: "Lisa", last_name: "Simpson", lastupdated: 1})
MERGE (s5:Person{id: 5, first_name: "Maggie", last_name: "Simpson", lastupdated: 1})
"""


# This is intended to test matching on more than one attribute.
# Lisa has 1 computer, Homer has 2, everyone else has no computers.
TEST_COMPUTERS = [
    {
        "Id": 1234,
        "RAM_GB": 16,
        "NumCores": 4,
        "name": "macbook-air",
        "LastName": "Simpson",
        "FirstName": "Lisa",
    },
    {
        "Id": 9876,
        "RAM_GB": 128,
        "NumCores": 32,
        "name": "server-in-the-closet",
        "LastName": "Simpson",
        "FirstName": "Homer",
    },
    {
        "Id": 1337,
        "RAM_GB": 2048,
        "NumCores": 1024,
        "name": "beefy-box",
        "LastName": "Simpson",
        "FirstName": "Homer",
    },
]
