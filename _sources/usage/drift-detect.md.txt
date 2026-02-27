# How to use Drift-Detection
Drift-Detection is a Cartography module that allows you to track changes of query results over time.

## A Quick Example: Tracking internet-exposed EC2 instances
The quickest way to get started using drift-detection is through an example. We showed you [how we mark EC2 instances as internet-exposed with Cartography analysis jobs](../dev/writing-analysis-jobs.md#example-job-which-of-my-ec2-instances-is-accessible-to-any-host-on-the-internet), and now we can use drift-detection to monitor when these instances are added or removed from our accounts over time!

### Setup
1. **Specify a** `${DRIFT_DETECTION_DIRECTORY}` on the machine that runs `cartography`. This can be any folder where you have read and write access to.

2. **Set up a folder structure** that looks like this:

	```
	${DRIFT_DETECTION_DIRECTORY}/
	|
	|----internet-exposure-query/
	|
	|----another-query-youre-interested-in/
	|
	|----yet-another-query-to-track-over-time/
	```

	As shown here, your `${DRIFT_DETECTION_DIRECTORY}` contains one or more `${QUERY_DIRECTORY}s`.

3. **Create a template file**

	Save the below contents as `${DRIFT_DETECTION_DIRECTORY}/internet-exposure-query/template.json`:

	```
	{
	  "name": "Internet Exposed EC2 Instances",
	  "validation_query": "match (n:EC2Instance) where n.exposed_internet = True return n.instancetype, n.privateipaddress, n.publicdnsname, n.exposed_internet_type"
	  "properties": [],
	  "results": []
	}
	```

	- `name` is a helpful name describing the query.
	- `validation_query` is the neo4j Cypher query to track over time. In this case, we have simply asked Neo4j to return `instancetype`, `privateipaddress`, `publicdnsname`, and `exposed_internet_type` from EC2Instances that Cartography has identified as accessible from the internet. When writing your own queries, note that drift-detection only supports `MATCH` queries (i.e. read operations). `MERGE` queries (write operations) are not supported.
	- `properties`: Leave this as an empty array. This field is a placeholder that will be filled.
	- `results`: Leave this as an empty array. This field is a placeholder that will be filled.

4. **Create a shortcut file**

	Save the below contents as `${DRIFT_DETECTION_DIRECTORY}/internet-exposure-query/shortcut.json`:

	```
	{
	  "name": "Internet Exposed EC2 Instances",
	  "shortcuts": {}
	}
	```

	`name` should match the `name` you specified in `template.json`.

All set 👍

### Running drift-detection

1. **Run `get-state` to save results of a query to json**

	Run `cartography-detectdrift get-state --neo4j-uri <your_neo4j_uri> --drift-detection-directory ${DRIFT_DETECTION_DIRECTORY}`

	The internet exposure query might return results that look like this:

	```
	| n.instancetype 	| n.privateipaddress 	| n.publicdnsname             	| n.exposed_internet_type 	|
	|----------------	|--------------------	|-----------------------------	|-------------------------	|
	| c4.large       	| 10.255.255.251     	| ec2.1.compute.amazonaws.com 	| [direct]                	|
	| t2.micro       	| 10.255.255.252     	| ec2.2.compute.amazonaws.com 	| [direct]                	|
	| c4.large       	| 10.255.255.253     	| ec2.3.compute.amazonaws.com 	| [direct, elb]                	|
	| t2.micro       	| 10.255.255.254     	| ec2.4.compute.amazonaws.com 	| [direct, elb]                 |

	```
	and we should now see a new JSON file `<unix_timestamp_1>.json` saved with information in this format:

	```
	{
	  "name": "Internet Exposed EC2 Instances",
	  "validation_query": "match (n:EC2Instance) where n.exposed_internet = True return n.instancetype, n.privateipaddress, n.publicdnsname, n.exposed_internet_type"
	  "properties": ["n.instancetype", "n.privateipaddress", "n.publicdnsname", "n.exposed_internet_type"],
	  "results": [
	    ["c4.large", "10.255.255.251", "ec2.1.compute.amazonaws.com", "direct"],
	    ["t2.micro", "10.255.255.252", "ec2.2.compute.amazonaws.com", "direct"],
	    ["c4.large", "10.255.255.253", "ec2.3.compute.amazonaws.com", "direct|elb"],
	    ["t2.micro", "10.255.255.254", "ec2.4.compute.amazonaws.com", "direct|elb"]
	  ]
	}
	```

	You can continually run `get-state` to save the results of a query to json. Each json state file will be named with the Unix timestamp of the time drift-detection was run.

2. **Comparing state files**

	Now let's say a couple days go by and some new EC2 Instances were added to our AWS account. We run the `get-state` command once more and get another file `<unix_timestamp_2>.json` which looks like this:

	```
	{
	  "name": "Internet Exposed EC2 Instances",
	  "validation_query": "match (n:EC2Instance) where n.exposed_internet = True return n.instancetype, n.privateipaddress, n.publicdnsname, n.exposed_internet_type""
	  "properties": ["n.instancetype", "n.privateipaddress", "n.publicdnsname", "n.exposed_internet_type"],
	  "results": [
	    ["t2.micro", "10.255.255.250", "ec2.0.compute.amazonaws.com", "direct"],
	    ["c4.large", "10.255.255.251", "ec2.1.compute.amazonaws.com", "direct"],
	    ["t2.micro", "10.255.255.252", "ec2.2.compute.amazonaws.com", "direct"],
	    ["c4.large", "10.255.255.253", "ec2.3.compute.amazonaws.com", "direct|elb"],
	    ["c4.large", "10.255.255.255", "ec2.5.compute.amazonaws.com", "direct|elb"]
	  ]
	}
	```

	It looks like our results list has slightly changed. We can use `drift-detection` to quickly diff the two files:


	`cartography-detectdrift get-drift --query-directory ${DRIFT_DETECTION_DIRECTORY}/internet-exposure-query --start-state <unix_timestamp_1>.json --end-state <unix_timestamp_2>.json`

	Finally, we should see the following messages pop up:

	```
	Query Name: Internet Exposed EC2 Instances
	Query Properties: ["n.instancetype", "n.privateipaddress", "n.publicdnsname", "n.exposed_internet_type"]

	New Query Results:

	n.instancetype: t2.micro
	n.privateipaddress: 10.255.255.250
	n.publicdnsname: ec2.0.compute.amazonaws.com
	n.exposed_internet_type: ['direct']

	n.instancetype: c4.large
	n.privateipaddress: 10.255.255.255
	n.publicdnsname: ec2.5.compute.amazonaws.com
	n.exposed_internet_type: ['direct', 'elb']

	Missing Query Results:

	n.instancetype: t2.micro
	n.privateipaddress: 10.255.255.253
	n.publicdnsname: ec2.4.compute.amazonaws.com
	n.exposed_internet_type: ['direct', 'elb']
	```

	This gives us a quick way to view infrastructure changes!

### Using shortcuts instead of filenames to diff files

It can be cumbersome to always type Unix timestamp filenames. To make this easier we can add `shortcuts` to diff two files without specifying the filename. This lets us bookmark certain states with whatever name we want.

1. **Adding shortcuts**

	Let's try adding shortcuts. We will name the first state "first-run" and the second state "second-run" with

	`cartography-detectdrift add-shortcut --shortcut first-run --file <unix_timestamp_1>.json`

	`cartography-detectdrift add-shortcut --shortcut second-run --file <unix_timestamp_2>.json`

	We can even use aliases instead of filenames when adding shortcuts!

	`cartography-detectdrift add-shortcut --shortcut baseline --file most-recent`

2. **Comparing state files with shortcuts**

	Now that we have shortcuts, we can now simply run

	`cartography-detectdrift get-drift --query-directory ${DRIFT_DETECTION_DIRECTORY}/internet-exposure-query --start-state first-run --end-state second-run`

Important note: Each execution of `get-state` will automatically generate a shortcut in each query directory, `most-recent`, which will refer to the last state file successfully created in that directory.
