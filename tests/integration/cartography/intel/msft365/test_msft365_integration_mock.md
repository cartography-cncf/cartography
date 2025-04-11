# 🧪 Running Microsoft 365 Mock Integration Tests in Cartography

This guide walks you through setting up and executing **mock integration tests** for Microsoft 365 in the Cartography project. These tests:

- Use real Neo4j instance (not in-memory)
- Mock Microsoft Graph API responses (no Azure account needed)

---

## 🛠️ Prerequisites

- Python 3.10+ with `venv` (or Anaconda)
- Docker (to run Neo4j)
- A working checkout of your Cartography fork

---

## ⚙️ 1. Set Up Neo4j with Docker

Run a local Neo4j container with default creds:

```bash
docker run \
  --name carto-neo4j \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/test1234 \
  -d neo4j:5.12
```

Confirm it's running:
```bash
docker ps
```

Neo4j will be accessible at:
- UI: http://localhost:7474
- Bolt: `bolt://localhost:7687`

---

## 🐍 2. Set Up Python Virtual Environment

From your project root:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## 🔐 3. Export Environment Variables

These are used to connect to Neo4j during tests:

```bash
export NEO4J_URI="bolt://localhost:7687"
export NEO4J_USER="neo4j"
export NEO4J_PASSWORD="test1234"
```

---

## 🧪 4. Run the Mock Tests

From the root of your Cartography repo:

```bash
PYTHONPATH=. \
NEO4J_URI=$NEO4J_URI \
NEO4J_USER=$NEO4J_USER \
NEO4J_PASSWORD=$NEO4J_PASSWORD \
./venv/bin/python -m unittest tests/integration/cartography/intel/msft365/test_msft365_integration_mock.py
```

Expected output (summary):

```
.🧪 TEST: Msft365Device mock sync starting...
✅ PASSED: Msft365Device mock sync
.
----------------------------------------------------------------------
Ran 2 tests in 0.xyz s

OK
```

---

## 🧯 Troubleshooting

| Problem | Fix |
|--------|-----|
| ❌ `device nodes = 0` | Ensure `load_node_data` is patched correctly in the test |
| ❌ Can't connect to Neo4j | Is Docker container running? Is Bolt on `localhost:7687`? |
| ❌ Test can't find fixture | Check that `devices.json` is in correct path: `tests/integration/cartography/intel/msft365/fixtures/` |

---

## ✅ Notes

- This test setup does **not** use real Azure/Microsoft365 credentials.
- Use this test to validate Cypher generation, Neo4j schema integration, and transformation logic independently.

---