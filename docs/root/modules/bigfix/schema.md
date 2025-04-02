## BigFix Schema

### BigfixComputer

Represents a computer tracked by BigFix.

| Field | Description |
|-------|--------------|
| firstseen| Timestamp of when a sync job first created this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| id | String. Internal BigFix ID. |
| activedirectorypath | Example: CN=my-server-2,CN=Computers,DC=example-corp,DC=net |
| agenttype | Example: Native |
| agentversion | Version of the BigFix agent. Example: 10.0.7.52 |
| averageevaluationcycle | Example: 106 (integer)|
| besrelayselectionmethod | Example: Manual |
| besrootserver | Example: bigfixroot.example.com (0) |
| bios | String value. Example: 06/25/2021 |
| computername | Example: my-server-2 |
| computertype | Example: Virtual, Physical |
| cpu | Example: 2300 MHz Xeon Gold 5218 |
| devicetype | Example: Server |
| dnsname | Example: my-server-2.example.com |
| enrollmentdatetime | The date time this asset was enrolled in BigFix. Example: 2022-04-06T18:54:01-07:00 |
| ipaddress | Example: 192.168.128.215 |
| ipv6address | Example: fe80:0:0:0:abcd:abcd:abcd:abcd |
| islocked | Boolean - whether this asset is locked |
| lastreporttime | Last reported datetime of this asset 2023-04-19T15:55:23Z |
| locationbyiprange | Example: SF |
| loggedonuser | Currently logged on username. Example: <none>, bartsimpson |
| macaddress | Example: 00-50-ab-cd-ab-cd |
| os | Example: Win2019 10.0.17763.3406 (1809) |
| providername | Example: VMware, On Premises |
| ram | Example: 16384 MB |
| relay | Example: mybigfixrelay.example.com |
| remotedesktopisenabled | Boolean - whether remote desktop is enabled |
| subnetaddress | Example: 192.168.128.0 |
| username | Example: <none>, bartsimpson |


#### Relationships

- A BigfixComputer is a resource of a BigfixRoot.
    ```
    (:BigfixRoot)-[:RESOURCE]->(:BigfixComputer)
    ```
