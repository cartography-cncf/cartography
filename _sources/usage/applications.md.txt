# Building around Cartography

This document shows patterns on how Cartography data fits in as part of a production system.

## DB driver

The quickest way to build an application around the graph is to use the Neo4j database driver and send queries at it:

![app-direct.png](../images/app-direct.png)


## API
A more mature application will want to define a formal API around it like this:

![app-with-api.png](../images/app-with-api.png)

This way, database queries are abstracted behind the questions that your users will want to ask the graph.

## As part of a data pipeline

It can be beneficial to periodically extract graph data into data warehouses like Hive. This way you can have historical data. Hive is also easily paired with Mode for dashboards.

![pipeline-hive-mode.png](../images/pipeline-hive-mode.png)

## Other useful dashboard options

[Neodash](https://github.com/neo4j-labs/neodash) ([video tutorial](https://www.youtube.com/watch?v=Ygzj0Y4cYm4)) is great for mocking up views on top of graph data and can help you build a "home-made CSPM" very quickly.

![pipeline-neodash.png](../images/pipeline-neodash.png)
