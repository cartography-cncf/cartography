# Your AI Agents Are in Production. Do You Know What They Can Access?

*How Cartography maps every AI agent in your cloud — from container image to IAM role to public FQDN — in a single graph query.*

---

Somewhere in your infrastructure right now, an AI agent is running. It was built by an application team that needed a customer support bot, or a code review assistant, or an internal search tool. It's sitting in an ECS task, behind a load balancer, with an IAM role that probably has more permissions than it needs.

You don't have it in a spreadsheet. Your CMDB doesn't know it exists. Your cloud security tool sees the container, the role, and the DNS record as three unrelated assets.

This is the AI governance gap. It's not that organizations lack security tools — it's that no single tool connects the dots between *what* an AI agent is, *where* it's running, *what it can access*, and *how it's reachable from the internet*. The blast radius of an AI agent isn't any one of those dimensions. It's the combination.

[Cartography](https://github.com/cartography-cncf/cartography) — the CNCF project that consolidates infrastructure assets and their relationships into a Neo4j graph — now closes that gap. With the new AIBOM (AI Bill of Materials) module, Cartography discovers AI agents inside container images and connects them to the infrastructure graph you already have: ECS tasks, IAM roles, VPCs, load balancers, and DNS records.

The result? One query that answers the question every security team needs to ask.

## The Query

Let's start with the payoff. Here's a single Cypher query that returns every AI agent in your AWS environment that's reachable from the internet, along with its public FQDN, IAM role, framework, declared tools, and connected LLMs:

```cypher
MATCH (agent:AIAgent)-[:DETECTED_IN]->(img:ECRImage)
      <-[:HAS_IMAGE]-(:ECSContainer)
      <-[:HAS_CONTAINER]-(task:ECSTask)
      -[:HAS_TASK_DEFINITION]->(:ECSTaskDefinition)
      -[:HAS_TASK_ROLE]->(role:AWSRole)
MATCH (task)-[:NETWORK_INTERFACE]->(:NetworkInterface)
      -[:PRIVATE_IP_ADDRESS]->(:EC2PrivateIp)
      <-[:EXPOSE]-(lb:AWSLoadBalancerV2)
      <-[:DNS_POINTS_TO]-(dns:AWSDNSRecord)
OPTIONAL MATCH (agent)-[:USES_TOOL]->(tool:AIBOMComponent)
OPTIONAL MATCH (agent)-[:USES_MODEL]->(model:AIBOMComponent)
RETURN agent.name        AS agent,
       agent.framework   AS framework,
       dns.name          AS fqdn,
       lb.dnsname        AS alb_endpoint,
       role.arn          AS iam_role,
       agent.file_path   AS source_file,
       collect(DISTINCT tool.name)  AS tools,
       collect(DISTINCT model.name) AS models
```

A real result might look like:

| agent | framework | fqdn | iam_role | tools | models |
|-------|-----------|------|----------|-------|--------|
| pydantic_ai.Agent | pydantic_ai | api.acme.com | arn:aws:iam::123:role/chat-service | [search_kb, create_ticket] | [openai:gpt-4.1-mini] |

That's one row per internet-exposed AI agent. Framework, URL, IAM role, tool access, and model — all in one view. No other tool gives you this today. Let's walk through how it works.

## Layer 1: What's Inside the Container?

The first challenge is *finding* the AI agents. They don't register themselves. There's no AWS service called "AI Agent Manager." They're just Python code inside a container image.

Cartography solves this with [AIBOM](https://github.com/cisco/aibom) — an AI Bill of Materials scanner that analyzes container images and produces a structured report of every AI component it finds. The scanner detects:

- **Agents** by framework — PydanticAI, LangChain, OpenAI Agents SDK, CrewAI, AutoGen, and more
- **Models** the agent connects to — `openai:gpt-4.1-mini`, `anthropic:claude-sonnet-4-20250514`, Bedrock endpoints
- **Tools** the agent declares — function calls, MCP servers, API integrations
- **Memory and retrieval** — vector stores, conversation history, RAG pipelines
- **Prompts and embeddings** — system prompts, embedding models

Detection goes deep. The scanner identifies the specific source file and line number where each component is defined. A report for a single image might look like:

```json
{
  "image_uri": "123456789.dkr.ecr.us-east-1.amazonaws.com/chat-service:v2.1",
  "components": {
    "agent": [{
      "name": "pydantic_ai.Agent",
      "framework": "pydantic_ai",
      "file_path": "/srv/app/chat/assistant.py",
      "line_number": 34,
      "label": "customer_assistant",
      "instance_id": "agent_main"
    }],
    "model": [{
      "name": "openai:gpt-4.1-mini",
      "category": "model",
      "instance_id": "model_primary"
    }],
    "tool": [{
      "name": "search_knowledge_base",
      "category": "tool",
      "instance_id": "tool_search"
    }]
  },
  "relationships": [
    {"relationship_type": "USES_LLM", "source": "agent_main", "target": "model_primary"},
    {"relationship_type": "USES_TOOL", "source": "agent_main", "target": "tool_search"}
  ]
}
```

Cartography's AIBOM intel module ingests these reports — from a local directory or an S3 bucket — and creates graph nodes for each component. Agents get an `AIAgent` label. Models get `AIModel`. Tools get `AITool`. The relationships between them (`USES_MODEL`, `USES_TOOL`, `USES_MEMORY`) are preserved exactly as the scanner detected them.

The critical join happens on **manifest digest**. The scanner records which ECR image digest it analyzed. Cartography's ECR module already has `ECRImage` nodes in the graph with those same digests. A single `DETECTED_IN` relationship bridges the two worlds:

```
(agent:AIAgent)-[:DETECTED_IN]->(img:ECRImage)
```

That one edge is the bridge from "AI component analysis" to "cloud infrastructure graph." Everything after this is traversal.

## Layer 2: Where Is It Running?

Cartography already knows your AWS infrastructure. If you're syncing ECS, EC2, and VPC data, the following graph already exists — no new scanning required.

**From image to running container:**
```
(img:ECRImage)<-[:HAS_IMAGE]-(container:ECSContainer)
    <-[:HAS_CONTAINER]-(task:ECSTask)
```

An `ECRImage` node is linked to every `ECSContainer` currently running that image (matched on digest). Each container belongs to an `ECSTask`, which is the actual running unit in ECS.

**From task to network:**
```
(task:ECSTask)-[:NETWORK_INTERFACE]->(eni:NetworkInterface)
    -[:PART_OF_SUBNET]->(subnet:EC2Subnet)
    -[:MEMBER_OF_AWS_VPC]->(vpc:AWSVpc)
```

The task's ENI tells you exactly which subnet and VPC it's in. Security groups come along for the ride:

```
(eni:NetworkInterface)-[:MEMBER_OF_EC2_SECURITY_GROUP]->(sg:EC2SecurityGroup)
```

**From network to load balancer to DNS:**
```
(eni:NetworkInterface)-[:PRIVATE_IP_ADDRESS]->(ip:EC2PrivateIp)
    <-[:EXPOSE]-(lb:AWSLoadBalancerV2)
    <-[:DNS_POINTS_TO]-(dns:AWSDNSRecord)
```

The ENI has a private IP. If that IP is registered as a target in an ALB/NLB, Cartography connects them via `EXPOSE`. And if a Route53 record (like `api.acme.com`) points to that load balancer, `DNS_POINTS_TO` completes the chain.

Every hop in this path already existed in Cartography before the AIBOM module was written. That's the graph advantage — new intel modules don't need to reinvent infrastructure discovery. They just connect to what's already there.

## Layer 3: What Can It Do?

The third dimension is identity and capabilities. What AWS permissions does this agent have? What tools can it invoke?

**IAM roles via the task definition:**
```
(task:ECSTask)-[:HAS_TASK_DEFINITION]->(td:ECSTaskDefinition)
    -[:HAS_TASK_ROLE]->(role:AWSRole)
    -[:HAS_EXECUTION_ROLE]->(execRole:AWSRole)
```

ECS has two distinct IAM roles. The **task role** is what the application code (your AI agent) assumes at runtime — this determines what AWS resources the agent can access. The **execution role** is what the ECS agent itself uses to pull images and write logs. Both matter for security, but the task role is the one that defines the agent's blast radius.

**Declared tools and models from the AIBOM:**
```
(agent:AIAgent)-[:USES_TOOL]->(tool:AITool)
(agent:AIAgent)-[:USES_MODEL]->(model:AIModel)
(agent:AIAgent)-[:USES_MEMORY]->(mem:AIMemory)
(agent:AIAgent)-[:IN_WORKFLOW]->(wf:AIBOMWorkflow)
```

These relationships capture what the scanner found in the source code. An agent that declares a `create_ticket` tool and connects to `gpt-4.1-mini` is a different risk profile than one that declares a `delete_database` tool and connects to a locally-hosted model.

## Putting It Together: Real Questions, Real Queries

With these three layers connected, answering governance questions becomes graph traversal.

### "Which internet-exposed agents have S3 write access?"

```cypher
MATCH (agent:AIAgent)-[:DETECTED_IN]->(:ECRImage)
      <-[:HAS_IMAGE]-(c:ECSContainer {exposed_internet: true})
MATCH (agent)-[:DETECTED_IN]->(:ECRImage)
      <-[:HAS_IMAGE]-(:ECSContainer)
      <-[:HAS_CONTAINER]-(:ECSTask)
      -[:HAS_TASK_DEFINITION]->(:ECSTaskDefinition)
      -[:HAS_TASK_ROLE]->(role:AWSRole)
WHERE role.arn CONTAINS 's3'
RETURN agent.name, agent.framework, role.arn
```

### "What's the blast radius of a compromised container image?"

Start at the image and fan out to everything it touches:

```cypher
MATCH (img:ECRImage {uri: $image_uri})
OPTIONAL MATCH (agent:AIAgent)-[:DETECTED_IN]->(img)
OPTIONAL MATCH (img)<-[:HAS_IMAGE]-(c:ECSContainer)
      <-[:HAS_CONTAINER]-(task:ECSTask)
OPTIONAL MATCH (task)-[:HAS_TASK_DEFINITION]->(:ECSTaskDefinition)
      -[:HAS_TASK_ROLE]->(role:AWSRole)
OPTIONAL MATCH (task)-[:NETWORK_INTERFACE]->(:NetworkInterface)
      -[:PRIVATE_IP_ADDRESS]->(:EC2PrivateIp)
      <-[:EXPOSE]-(lb:AWSLoadBalancerV2)
      <-[:DNS_POINTS_TO]-(dns:AWSDNSRecord)
RETURN img.uri, collect(DISTINCT agent.name) AS agents,
       collect(DISTINCT role.arn) AS iam_roles,
       collect(DISTINCT dns.name) AS fqdns,
       collect(DISTINCT task.id) AS running_tasks
```

### "Are any agents running without a scoped task role?"

Agents using the execution role (or no task role at all) are a red flag — it means the agent might be running with the ECS infrastructure role's permissions:

```cypher
MATCH (agent:AIAgent)-[:DETECTED_IN]->(:ECRImage)
      <-[:HAS_IMAGE]-(:ECSContainer)
      <-[:HAS_CONTAINER]-(:ECSTask)
      -[:HAS_TASK_DEFINITION]->(td:ECSTaskDefinition)
WHERE td.task_role_arn IS NULL
RETURN agent.name, agent.framework, td.id AS task_definition
```

### "Show me all agents reachable at *.acme.com"

Trace backwards from DNS to discover what's behind a domain:

```cypher
MATCH (dns:AWSDNSRecord)
WHERE dns.name ENDS WITH '.acme.com'
MATCH (dns)-[:DNS_POINTS_TO]->(lb:AWSLoadBalancerV2)
      -[:EXPOSE]->(:EC2PrivateIp)
      <-[:PRIVATE_IP_ADDRESS]-(:NetworkInterface)
      <-[:NETWORK_INTERFACE]-(task:ECSTask)
      -[:HAS_CONTAINER]->(:ECSContainer)
      -[:HAS_IMAGE]->(img:ECRImage)
      <-[:DETECTED_IN]-(agent:AIAgent)
RETURN dns.name AS fqdn, agent.name, agent.framework
```

### "Which agents use external LLM APIs and also have database access?"

Cross-correlate model connections with network position:

```cypher
MATCH (agent:AIAgent)-[:USES_MODEL]->(model:AIBOMComponent)
WHERE model.name STARTS WITH 'openai:' OR model.name STARTS WITH 'anthropic:'
MATCH (agent)-[:DETECTED_IN]->(:ECRImage)
      <-[:HAS_IMAGE]-(:ECSContainer)
      <-[:HAS_CONTAINER]-(task:ECSTask)
      -[:NETWORK_INTERFACE]->(:NetworkInterface)
      -[:MEMBER_OF_EC2_SECURITY_GROUP]->(sg:EC2SecurityGroup)
WHERE sg.name CONTAINS 'rds' OR sg.name CONTAINS 'database'
RETURN agent.name, model.name AS external_model,
       collect(sg.name) AS db_security_groups
```

## The Shortcut: Pre-Computed Exposure

Running multi-hop traversals is powerful but expensive for dashboards. Cartography includes an analysis job that pre-computes internet exposure, walking the path from `AWSLoadBalancerV2` through `EC2PrivateIp`, `NetworkInterface`, and `ECSTask` down to `ECSContainer`, setting `exposed_internet = true` on every container behind a public load balancer.

This enables fast one-hop queries for alerting and dashboards:

```cypher
MATCH (agent:AIAgent)-[:DETECTED_IN]->(:ECRImage)
      <-[:HAS_IMAGE]-(c:ECSContainer {exposed_internet: true})
RETURN agent.name, agent.framework, c.exposed_internet_type
```

No traversal. No joins. Just a property lookup. This is how you build a real-time dashboard of internet-exposed AI agents.

## Setting It Up

If you're already running Cartography with AWS sync, you're most of the way there. The infrastructure graph — ECS, EC2, IAM, Route53, ELB — is already populated.

**Step 1: Scan your ECR images.** Run the [cisco-aibom](https://github.com/cisco/aibom) scanner against your container images. Output the results to an S3 bucket or a local directory.

**Step 2: Configure Cartography.** Add the AIBOM data source to your Cartography config:

```bash
# From S3
cartography --aibom-s3-bucket my-aibom-results --aibom-s3-prefix scans/latest/

# Or from a local directory
cartography --aibom-results-dir /path/to/aibom/results/
```

**Step 3: Run a sync.** Cartography's AIBOM module will:
1. Parse every AIBOM JSON report it finds
2. Resolve image URIs to ECR manifest digests already in the graph
3. Create `AIAgent`, `AIModel`, `AITool`, and other component nodes
4. Connect them to `ECRImage` nodes via `DETECTED_IN`
5. Create inter-component relationships (`USES_MODEL`, `USES_TOOL`, etc.)

The manifest digest is the bridge. If Cartography has already synced your ECR repositories, the AIBOM module will automatically match scanned images to their graph nodes. From there, the full traversal path — through ECS, to IAM, to VPC, to load balancer, to DNS — lights up instantly.

**Step 4: Query.** Open Neo4j Browser, paste the hero query, and see every AI agent in your infrastructure mapped to its full operational context.

## The Graph Advantage

Any container scanner can tell you "this image contains PydanticAI." Any cloud security tool can tell you "this ECS task has IAM role X." Any DNS tool can tell you "api.acme.com points to this ALB."

The insight isn't in any one of those facts. It's in the *path* between them:

```
AWSDNSRecord → AWSLoadBalancerV2 → EC2PrivateIp → NetworkInterface
  → ECSTask → ECSContainer → ECRImage → AIAgent → AITool / AIModel
               ↓
         ECSTaskDefinition → AWSRole
```

That path is the blast radius. That path is what you need to govern. And that path only exists when all your infrastructure data lives in the same graph.

Cartography has been building that graph across 50+ platforms for years. The AIBOM module doesn't reinvent infrastructure discovery — it adds one new edge (`DETECTED_IN`) and connects to everything that's already there. That's the power of a graph-based approach to security: every new data source makes the whole graph more valuable.

Your AI agents are in production. Now you can see them.

---

*[Cartography](https://github.com/cartography-cncf/cartography) is a CNCF project that consolidates infrastructure assets and their relationships in an intuitive graph view powered by Neo4j. Get started at [cartography-cncf.github.io/cartography](https://cartography-cncf.github.io/cartography).*
