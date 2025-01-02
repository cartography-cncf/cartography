## Sample queries

Note: you might want to add `LIMIT 30` at the end of these queries to make sure they return
quickly in case you have a large graph.

### Which AWS IAM roles have admin permissions in my accounts?
```
MATCH (stmt:AWSPolicyStatement)--(pol:AWSPolicy)--(principal:AWSPrincipal)--(a:AWSAccount)
WHERE stmt.effect = "Allow"
AND any(x IN stmt.action WHERE x = '*')
RETURN *
```

### Which AWS IAM roles in my environment have the ability to delete policies?
```
MATCH (stmt:AWSPolicyStatement)--(pol:AWSPolicy)--(principal:AWSPrincipal)--(acc:AWSAccount)
WHERE stmt.effect = "Allow"
AND any(x IN stmt.action WHERE x="iam:DeletePolicy" )
RETURN *
```

Note: can replace "`iam:DeletePolicy`" to search for other IAM actions.


### Which AWS IAM roles in my environment have an action that contains the word "create"?
```
MATCH (stmt:AWSPolicyStatement)--(pol:AWSPolicy)--(principal:AWSPrincipal)--(acc:AWSAccount)
WHERE stmt.effect = "Allow"
AND any(x IN stmt.action WHERE toLower(x) contains "create")
RETURN *
```

### What [RDS](https://aws.amazon.com/rds/) instances are installed in my [AWS](https://aws.amazon.com/) accounts?
```
MATCH (aws:AWSAccount)-[r:RESOURCE]->(rds:RDSInstance)
return *
```

### Which RDS instances have [encryption](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/Overview.Encryption.html) turned off?
```
MATCH (a:AWSAccount)-[:RESOURCE]->(rds:RDSInstance{storage_encrypted:false})
return a.name, rds.id
```

### Which [EC2](https://aws.amazon.com/ec2/) instances are exposed (directly or indirectly) to the internet?
```
MATCH (instance:EC2Instance{exposed_internet: true})
RETURN instance.instanceid, instance.publicdnsname
```

### Which [ELB](https://aws.amazon.com/elasticloadbalancing/) LoadBalancers are internet accessible?
```
MATCH (elb:LoadBalancer{exposed_internet: true})—->(listener:ELBListener)
RETURN elb.dnsname, listener.port
ORDER by elb.dnsname, listener.port
```

### Which [ELBv2](https://aws.amazon.com/elasticloadbalancing/) LoadBalancerV2s (Application Load Balancers) are internet accessible?
```
MATCH (elbv2:LoadBalancerV2{exposed_internet: true})—->(listener:ELBV2Listener)
RETURN elbv2.dnsname, listener.port
ORDER by elbv2.dnsname, listener.port
```

### Which [S3](https://aws.amazon.com/s3/) buckets have a policy granting any level of anonymous access to the bucket?
```
MATCH (s:S3Bucket)
WHERE s.anonymous_access = true
RETURN s
```

### How many unencrypted RDS instances do I have in all my AWS accounts?

```
MATCH (a:AWSAccount)-[:RESOURCE]->(rds:RDSInstance)
WHERE rds.storage_encrypted = false
return a.name as AWSAccount, count(rds) as UnencryptedInstances
```

### What languages are used in a given GitHub repository?
```
MATCH (:GitHubRepository{name:"myrepo"})-[:LANGUAGE]->(lang:ProgrammingLanguage)
RETURN lang.name
```

### What are the dependencies used in a given GitHub repository?
```
MATCH (:GitHubRepository{name:"myrepo"})-[edge:REQUIRES]->(dep:Dependency)
RETURN dep.name, edge.specifier, dep.version
```

If you want to filter to just e.g. Python libraries:
```
MATCH (:GitHubRepository{name:"myrepo"})-[edge:REQUIRES]->(dep:Dependency:PythonLibrary)
RETURN dep.name, edge.specifier, dep.version
```

### Given a dependency, which GitHub repos depend on it?
Using boto3 as an example dependency:
```
MATCH (dep:Dependency:PythonLibrary{name:"boto3"})<-[req:REQUIRES]-(repo:GitHubRepository)
RETURN repo.name, req.specifier, dep.version
```

### What are all the dependencies used across all GitHub repos?
Just the list of dependencies and their versions:
```
MATCH (dep:Dependency)
RETURN DISTINCT dep.name AS name, dep.version AS version
ORDER BY dep.name
```

With info about which repos are using them:
```
MATCH (repo:GitHubRepository)-[edge:REQUIRES]->(dep:Dependency)
RETURN repo.name, dep.name, edge.specifier, dep.version
```
Lyft ingests this information into our internal data stack,
which has enabled us to throw BI tooling on top for easy reporting -
this is highly recommended!
