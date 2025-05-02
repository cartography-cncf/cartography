## Sample queries

Note: you might want to add `LIMIT 30` at the end of these queries to make sure they RETURN
quickly in case you have a large graph.

### Which AWS IAM roles have admin permissions in my accounts?
```cypher
MATCH (stmt:AWSPolicyStatement)--(pol:AWSPolicy)--(principal:AWSPrincipal)--(a:AWSAccount)
WHERE stmt.effect = "Allow"
AND any(x IN stmt.action WHERE x = '*')
RETURN *
```
[test it locally](http://localhost:7474/browser/?preselectAuthMethod=NO_AUTH&db=neo4j&connectURL=bolt://neo4j:neo4j@localhost:7474&cmd=edit&arg=MATCH%20%28stmt%3AAWSPolicyStatement%29--%28pol%3AAWSPolicy%29--%28principal%3AAWSPrincipal%29--%28a%3AAWSAccount%29%0AWHERE%20stmt.effect%20%3D%20%22Allow%22%0AAND%20any%28x%20IN%20stmt.action%20WHERE%20x%20%3D%20%27%2A%27%29%0ARETURN%20%2A)

### Which AWS IAM roles in my environment have the ability to delete policies?
```cypher
MATCH (stmt:AWSPolicyStatement)--(pol:AWSPolicy)--(principal:AWSPrincipal)--(acc:AWSAccount)
WHERE stmt.effect = "Allow"
AND any(x IN stmt.action WHERE x="iam:DeletePolicy" )
RETURN *
```
[test it locally](http://localhost:7474/browser/?preselectAuthMethod=NO_AUTH&db=neo4j&connectURL=bolt://neo4j:neo4j@localhost:7474&cmd=edit&arg=MATCH%20%28stmt%3AAWSPolicyStatement%29--%28pol%3AAWSPolicy%29--%28principal%3AAWSPrincipal%29--%28acc%3AAWSAccount%29%0AWHERE%20stmt.effect%20%3D%20%22Allow%22%0AAND%20any%28x%20IN%20stmt.action%20WHERE%20x%3D%22iam%3ADeletePolicy%22%20%29%0ARETURN%20%2A)

Note: can replace "`iam:DeletePolicy`" to search for other IAM actions.


### Which AWS IAM roles in my environment have an action that contains the word "create"?
```cypher
MATCH (stmt:AWSPolicyStatement)--(pol:AWSPolicy)--(principal:AWSPrincipal)--(acc:AWSAccount)
WHERE stmt.effect = "Allow"
AND any(x IN stmt.action WHERE toLower(x) contains "create")
RETURN *
```
[test it locally](http://localhost:7474/browser/?preselectAuthMethod=NO_AUTH&db=neo4j&connectURL=bolt://neo4j:neo4j@localhost:7474&cmd=edit&arg=MATCH%20%28stmt%3AAWSPolicyStatement%29--%28pol%3AAWSPolicy%29--%28principal%3AAWSPrincipal%29--%28acc%3AAWSAccount%29%0AWHERE%20stmt.effect%20%3D%20%22Allow%22%0AAND%20any%28x%20IN%20stmt.action%20WHERE%20toLower%28x%29%20contains%20%22create%22%29%0ARETURN%20%2A)

### What [RDS](https://aws.amazon.com/rds/) instances are installed in my [AWS](https://aws.amazon.com/) accounts?
```cypher
MATCH (aws:AWSAccount)-[r:RESOURCE]->(rds:RDSInstance)
RETURN *
```
[test it locally](http://localhost:7474/browser/?preselectAuthMethod=NO_AUTH&db=neo4j&connectURL=bolt://neo4j:neo4j@localhost:7474&cmd=edit&arg=MATCH%20%28aws%3AAWSAccount%29-%5Br%3ARESOURCE%5D-%3E%28rds%3ARDSInstance%29%0ARETURN%20%2A)

### Which RDS instances have [encryption](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/Overview.Encryption.html) turned off?
```cypher
MATCH (a:AWSAccount)-[:RESOURCE]->(rds:RDSInstance{storage_encrypted:false})
RETURN a.name, rds.id
```
[test it locally](http://localhost:7474/browser/?preselectAuthMethod=NO_AUTH&db=neo4j&connectURL=bolt://neo4j:neo4j@localhost:7474&cmd=edit&arg=MATCH%20%28a%3AAWSAccount%29-%5B%3ARESOURCE%5D-%3E%28rds%3ARDSInstance%7Bstorage_encrypted%3Afalse%7D%29%0ARETURN%20a.name%2C%20rds.id)

### Which [EC2](https://aws.amazon.com/ec2/) instances are exposed (directly or indirectly) to the internet?
```cypher
MATCH (instance:EC2Instance{exposed_internet: true})
RETURN instance.instanceid, instance.publicdnsname
```
[test it locally](http://localhost:7474/browser/?preselectAuthMethod=NO_AUTH&db=neo4j&connectURL=bolt://neo4j:neo4j@localhost:7474&cmd=edit&arg=MATCH%20%28instance%3AEC2Instance%7Bexposed_internet%3A%20true%7D%29%0ARETURN%20instance.instanceid%2C%20instance.publicdnsname)

### Which open ports are internet accesible from [SecurityGroups](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-security-groups.html)
```cypher
    MATCH (open)-[:MEMBER_OF_EC2_SECURITY_GROUP]->(sg:EC2SecurityGroup)
    MATCH (sg)<-[:MEMBER_OF_EC2_SECURITY_GROUP]-(ipi:IpPermissionInbound)
    MATCH (ipi)<--(ir:IpRange)
    WHERE ir.range = "0.0.0.0/0"
    OPTIONAL MATCH (dns:AWSDNSRecord)-[:DNS_POINTS_TO]->(lb)
    WHERE open.scheme = "internet-facing"
    RETURN DISTINCT ipi.toport as port, open.id, sg.id
```
[test it locally](http://localhost:7474/browser/?preselectAuthMethod=NO_AUTH&db=neo4j&connectURL=bolt://neo4j:neo4j@localhost:7474&cmd=edit&arg=MATCH%20%28open%29-%5B%3AMEMBER_OF_EC2_SECURITY_GROUP%5D-%3E%28sg%3AEC2SecurityGroup%29%0A%20%20%20%20MATCH%20%28sg%29%3C-%5B%3AMEMBER_OF_EC2_SECURITY_GROUP%5D-%28ipi%3AIpPermissionInbound%29%0A%20%20%20%20MATCH%20%28ipi%29%3C--%28ir%3AIpRange%29%0A%20%20%20%20WHERE%20ir.range%20%3D%20%220.0.0.0%2F0%22%0A%20%20%20%20OPTIONAL%20MATCH%20%28dns%3AAWSDNSRecord%29-%5B%3ADNS_POINTS_TO%5D-%3E%28lb%29%0A%20%20%20%20WHERE%20open.scheme%20%3D%20%22internet-facing%22%0A%20%20%20%20RETURN%20DISTINCT%20ipi.toport%20as%20port%2C%20open.id%2C%20sg.id)

### Which [ELB](https://aws.amazon.com/elasticloadbalancing/) LoadBalancers are internet accessible?
```cypher
MATCH (elb:LoadBalancer{exposed_internet: true})—->(listener:ELBListener)
RETURN elb.dnsname, listener.port
ORDER by elb.dnsname, listener.port
```
[test it locally](http://localhost:7474/browser/?preselectAuthMethod=NO_AUTH&db=neo4j&connectURL=bolt://neo4j:neo4j@localhost:7474&cmd=edit&arg=MATCH%20%28elb%3ALoadBalancer%7Bexposed_internet%3A%20true%7D%29%E2%80%94-%3E%28listener%3AELBListener%29%0ARETURN%20elb.dnsname%2C%20listener.port%0AORDER%20by%20elb.dnsname%2C%20listener.port)

### Which [ELBv2](https://aws.amazon.com/elasticloadbalancing/) LoadBalancerV2s (Application Load Balancers) are internet accessible?
```cypher
MATCH (elbv2:LoadBalancerV2{exposed_internet: true})—->(listener:ELBV2Listener)
RETURN elbv2.dnsname, listener.port
ORDER by elbv2.dnsname, listener.port
```
[test it locally](http://localhost:7474/browser/?preselectAuthMethod=NO_AUTH&db=neo4j&connectURL=bolt://neo4j:neo4j@localhost:7474&cmd=edit&arg=MATCH%20%28elbv2%3ALoadBalancerV2%7Bexposed_internet%3A%20true%7D%29%E2%80%94-%3E%28listener%3AELBV2Listener%29%0ARETURN%20elbv2.dnsname%2C%20listener.port%0AORDER%20by%20elbv2.dnsname%2C%20listener.port)

### Which open ports are internet accesible from ELB or ELBv2?
```cypher
    MATCH (elb:LoadBalancer{exposed_internet: true})—->(listener:ELBListener)
    RETURN DISTINCT elb.dnsname as dnsname, listener.port as port
    UNION
    MATCH (lb:LoadBalancerV2)-[:ELBV2_LISTENER]->(l:ELBV2Listener)
    WHERE lb.scheme = "internet-facing"
    RETURN DISTINCT lb.dnsname as dnsname, l.port as port
```
[test it locally](http://localhost:7474/browser/?preselectAuthMethod=NO_AUTH&db=neo4j&connectURL=bolt://neo4j:neo4j@localhost:7474&cmd=edit&arg=MATCH%20%28elb%3ALoadBalancer%7Bexposed_internet%3A%20true%7D%29%E2%80%94-%3E%28listener%3AELBListener%29%0A%20%20%20%20RETURN%20DISTINCT%20elb.dnsname%20as%20dnsname%2C%20listener.port%20as%20port%20%0A%20%20%20%20UNION%0A%20%20%20%20MATCH%20%28lb%3ALoadBalancerV2%29-%5B%3AELBV2_LISTENER%5D-%3E%28l%3AELBV2Listener%29%0A%20%20%20%20WHERE%20lb.scheme%20%3D%20%22internet-facing%22%0A%20%20%20%20RETURN%20DISTINCT%20lb.dnsname%20as%20dnsname%2C%20l.port%20as%20port)

### Find everything about an IP Address
```cypher
MATCH (n:EC2PrivateIp)-[r]-(n2)
WHERE n.public_ip = $neodash_ip
RETURN n, r, n2

UNION MATCH(n:EC2Instance)-[r]-(n2)
WHERE n.publicipaddress = $neodash_ip
RETURN  n, r, n2

UNION MATCH(n:NetworkInterface)-[r]-(n2)
WHERE n.public_ip = $neodash_ip
RETURN n, r, n2

UNION MATCH(n:ElasticIPAddress)-[r]-(n2)
WHERE n.public_ip = $neodash_ip
RETURN n, r, n2
```
[test it locally](http://localhost:7474/browser/?preselectAuthMethod=NO_AUTH&db=neo4j&connectURL=bolt://neo4j:neo4j@localhost:7474&cmd=edit&arg=MATCH%20%28n%3AEC2PrivateIp%29-%5Br%5D-%28n2%29%0AWHERE%20n.public_ip%20%3D%20%24neodash_ip%0ARETURN%20n%2C%20r%2C%20n2%0A%0AUNION%20MATCH%28n%3AEC2Instance%29-%5Br%5D-%28n2%29%0AWHERE%20n.publicipaddress%20%3D%20%24neodash_ip%0ARETURN%20%20n%2C%20r%2C%20n2%0A%0AUNION%20MATCH%28n%3ANetworkInterface%29-%5Br%5D-%28n2%29%0AWHERE%20n.public_ip%20%3D%20%24neodash_ip%0ARETURN%20n%2C%20r%2C%20n2%0A%0AUNION%20MATCH%28n%3AElasticIPAddress%29-%5Br%5D-%28n2%29%0AWHERE%20n.public_ip%20%3D%20%24neodash_ip%0ARETURN%20n%2C%20r%2C%20n2)

### Which [S3](https://aws.amazon.com/s3/) buckets have a policy granting any level of anonymous access to the bucket?
```cypher
MATCH (s:S3Bucket)
WHERE s.anonymous_access = true
RETURN s
```
[test it locally](http://localhost:7474/browser/?preselectAuthMethod=NO_AUTH&db=neo4j&connectURL=bolt://neo4j:neo4j@localhost:7474&cmd=edit&arg=MATCH%20%28s%3AS3Bucket%29%0AWHERE%20s.anonymous_access%20%3D%20true%0ARETURN%20s)

### How many unencrypted RDS instances do I have in all my AWS accounts?

```cypher
MATCH (a:AWSAccount)-[:RESOURCE]->(rds:RDSInstance)
WHERE rds.storage_encrypted = false
RETURN a.name as AWSAccount, count(rds) as UnencryptedInstances
```
[test it locally](http://localhost:7474/browser/?preselectAuthMethod=NO_AUTH&db=neo4j&connectURL=bolt://neo4j:neo4j@localhost:7474&cmd=edit&arg=MATCH%20%28a%3AAWSAccount%29-%5B%3ARESOURCE%5D-%3E%28rds%3ARDSInstance%29%0AWHERE%20rds.storage_encrypted%20%3D%20false%0ARETURN%20a.name%20as%20AWSAccount%2C%20count%28rds%29%20as%20UnencryptedInstances)

### What languages are used in a given GitHub repository?
```cypher
MATCH (:GitHubRepository{name:"myrepo"})-[:LANGUAGE]->(lang:ProgrammingLanguage)
RETURN lang.name
```
[test it locally](http://localhost:7474/browser/?preselectAuthMethod=NO_AUTH&db=neo4j&connectURL=bolt://neo4j:neo4j@localhost:7474&cmd=edit&arg=MATCH%20%28%3AGitHubRepository%7Bname%3A%22myrepo%22%7D%29-%5B%3ALANGUAGE%5D-%3E%28lang%3AProgrammingLanguage%29%0ARETURN%20lang.name)

### What are the dependencies used in a given GitHub repository?
```cypher
MATCH (:GitHubRepository{name:"myrepo"})-[edge:REQUIRES]->(dep:Dependency)
RETURN dep.name, edge.specifier, dep.version
```
[test it locally](http://localhost:7474/browser/?preselectAuthMethod=NO_AUTH&db=neo4j&connectURL=bolt://neo4j:neo4j@localhost:7474&cmd=edit&arg=MATCH%20%28%3AGitHubRepository%7Bname%3A%22myrepo%22%7D%29-%5Bedge%3AREQUIRES%5D-%3E%28dep%3ADependency%29%0ARETURN%20dep.name%2C%20edge.specifier%2C%20dep.version)

If you want to filter to just e.g. Python libraries:
```cypher
MATCH (:GitHubRepository{name:"myrepo"})-[edge:REQUIRES]->(dep:Dependency:PythonLibrary)
RETURN dep.name, edge.specifier, dep.version
```
[test it locally](http://localhost:7474/browser/?preselectAuthMethod=NO_AUTH&db=neo4j&connectURL=bolt://neo4j:neo4j@localhost:7474&cmd=edit&arg=MATCH%20%28%3AGitHubRepository%7Bname%3A%22myrepo%22%7D%29-%5Bedge%3AREQUIRES%5D-%3E%28dep%3ADependency%3APythonLibrary%29%0ARETURN%20dep.name%2C%20edge.specifier%2C%20dep.version)

### Given a dependency, which GitHub repos depend on it?
Using boto3 as an example dependency:
```cypher
MATCH (dep:Dependency:PythonLibrary{name:"boto3"})<-[req:REQUIRES]-(repo:GitHubRepository)
RETURN repo.name, req.specifier, dep.version
```
[test it locally](http://localhost:7474/browser/?preselectAuthMethod=NO_AUTH&db=neo4j&connectURL=bolt://neo4j:neo4j@localhost:7474&cmd=edit&arg=MATCH%20%28dep%3ADependency%3APythonLibrary%7Bname%3A%22boto3%22%7D%29%3C-%5Breq%3AREQUIRES%5D-%28repo%3AGitHubRepository%29%0ARETURN%20repo.name%2C%20req.specifier%2C%20dep.version)

### What are all the dependencies used across all GitHub repos?
Just the list of dependencies and their versions:
```cypher
MATCH (dep:Dependency)
RETURN DISTINCT dep.name AS name, dep.version AS version
ORDER BY dep.name
```
[test it locally](http://localhost:7474/browser/?preselectAuthMethod=NO_AUTH&db=neo4j&connectURL=bolt://neo4j:neo4j@localhost:7474&cmd=edit&arg=MATCH%20%28dep%3ADependency%29%0ARETURN%20DISTINCT%20dep.name%20AS%20name%2C%20dep.version%20AS%20version%0AORDER%20BY%20dep.name)

With info about which repos are using them:
```cypher
MATCH (repo:GitHubRepository)-[edge:REQUIRES]->(dep:Dependency)
RETURN repo.name, dep.name, edge.specifier, dep.version
```
[test it locally](http://localhost:7474/browser/?preselectAuthMethod=NO_AUTH&db=neo4j&connectURL=bolt://neo4j:neo4j@localhost:7474&cmd=edit&arg=MATCH%20%28repo%3AGitHubRepository%29-%5Bedge%3AREQUIRES%5D-%3E%28dep%3ADependency%29%0ARETURN%20repo.name%2C%20dep.name%2C%20edge.specifier%2C%20dep.version)
