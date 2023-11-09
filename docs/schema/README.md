# Cartography Schema

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [ℹ️ Quick notes on notation](#-quick-notes-on-notation)
- [Amazon Web Services](#amazon-web-services)
- [Google Cloud Platform](#google-cloud-platform)
- [GSuite](#gsuite)
- [CRXcavator Platform](#crxcavator-platform)
- [Microsoft Azure](#microsoft-azure)
- [Kubernetes](#kubernetes)
- [More to come!](#more-to-come)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

## ℹ️ Quick notes on notation
- **Bolded words** in the schema tables indicate that this field is indexed, so your queries will run faster if you use these fields.

- This isn't proper Neo4j syntax, but for the purpose of this document we will use this notation:

	```
	(NodeTypeA)-[RELATIONSHIP_R]->(NodeTypeB, NodeTypeC, NodeTypeD, NodeTypeE)
	```

	to mean a shortened version of this:

	```
	(NodeTypeA)-[RELATIONSHIP_R]->(NodeTypeB)
	(NodeTypeA)-[RELATIONSHIP_R]->(NodeTypeC)
	(NodeTypeA)-[RELATIONSHIP_R]->(NodeTypeD)
	(NodeTypeA)-[RELATIONSHIP_R]->(NodeTypeE)
	```


	In words, this means that `NodeTypeA` has `RELATIONSHIP_R` pointing to `NodeTypeB`, and `NodeTypeA` has `RELATIONSHIP_R` pointing to `NodeTypeC`.

- In these docs, more specific nodes will be decorated with `GenericNode::SpecificNode` notation.  For example, if we have a `Car` node and a `RaceCar` node, we will refer to the `RaceCar` as `Car::RaceCar`.

## Amazon Web Services
- Click [here](aws.md)

## Google Cloud Platform
- Click [here](gcp.md)

## GSuite
- Click [here](gsuite.md)

## CRXcavator Platform
- Click [here](crxcavator.md)

## Microsoft Azure
- Click [here](azure.md)

## Kubernetes
- Click [here](kubernetes.md)

## SyncMetadata
- Click [here](syncmetadata.md)

## Semgrep
- Click [here](https://lyft.github.io/cartography/modules/semgrep/schema.html)

## More to come!
👍
