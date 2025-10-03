# Cartography Rules

With the `cartography-rules` command, we provide a set of pre-defined queries that let you evaluate your environment against common security frameworks, along with community-curated rules.


## Our opinionated approach

These rules are designed from an attacker’s perspective. For each framework technique, we ask: "What does an attacker actually need to execute this technique?"

Our queries surface opportunities that enable attacks at all stages of the kill chain: initial access, lateral movement, data exfiltration, and beyond.

**What we don’t do**: impose thresholds or arbitrary expectations.
Every organization has different risk tolerances. Saying “you should have at most 5 admin roles” is overly simplistic and rarely useful.

Instead, we focus on providing _facts_ and context so you can make your own informed decisions about your environment.
- If a query returns no results, you’ve successfully eliminated obvious attack opportunities for that technique.
- If it does return findings, you now have a clear list of potential targets for attackers.


## Why do it this way

For some organizations, showing an EC2 security group that allows inbound internet traffic from the public internet even if there are no compute instances attached to it may be useful because someone in the future may attach a compute instance to it. For others, this is noise.

Our goal is to build a comprehensive set of facts that can extract the full picture of your environment.


## Setup

```bash
export NEO4J_URI=bolt://localhost:7687 # or your Neo4j URI
export NEO4J_USER=neo4j # or your username
export NEO4J_DATABASE=neo4j

# Store the Neo4j password in an environment variable. You can name this anything you want.

set +o history # avoid storing the password in the shell history; can also use something like 1password CLI.
export NEO4J_PASSWORD=password
set -o history # turn shell history back on
```

## Usage

### `list`
See available frameworks
```bash
cartography-rules list
```

See available requirements for a framework
```bash
cartography-rules list mitre-attack
```

See available facts for a requirement
```bash
cartography-rules list mitre-attack t1190
```

### `run`

Run all frameworks
```bash
cartography-rules run all
```

Run a specific framework
```bash
cartography-rules run mitre-attack
```

Run a specific requirement on a framework
```bash
cartography-rules run mitre-attack t1190
```

Run a specific fact on a requirement

```bash
cartography-rules run mitre-attack t1190 aws_rds_public_access
```


### Authentication Options

Use a custom environment variable for the password:
```bash
cartography-rules run mitre-attack --neo4j-password-env-var MY_NEO4J_PASSWORD
```

Use interactive password prompt:
```bash
cartography-rules run mitre-attack --neo4j-password-prompt
```

Run a specific framework and output as JSON
```bash
cartography-rules run mitre-attack --output json
```

### Tab completion

Note that you can TAB complete. Install it with

```bash
cartography-rules --install-completion
```

and then restart your shell and then you can get TAB completion like:

```bash
cartography-rules run <TAB>
```

and then it will show you all the available frameworks.
