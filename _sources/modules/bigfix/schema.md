<!-- Generated from the data model. Do not edit manually. -->

## Bigfix Schema

```mermaid
graph LR
    BigfixRoot -- RESOURCE --> BigfixComputer
```

### BigfixComputer

A computer tracked by BigFix.

#### Properties

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | Internal BigFix ID. |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| activedirectorypath |  | Active Directory path. |
| agenttype |  | BigFix agent type. |
| agentversion |  | BigFix agent version. |
| averageevaluationcycle |  | Average evaluation cycle. |
| besrelayselectionmethod |  | BES relay selection method. |
| besrootserver |  | BES root server. |
| bios |  | BIOS information. |
| computername | Yes | Computer name. |
| computertype |  | Computer type, such as virtual or physical. |
| cpu |  | CPU information. |
| devicetype |  | Device type, such as server. |
| distancetobesrelay |  | Distance to the BES relay. |
| dnsname |  | DNS name. |
| enrollmentdatetime |  | Timestamp when the computer enrolled in BigFix. |
| freespaceonsystemdrive |  | Free space on the system drive. |
| ipaddress |  | IPv4 address. |
| ipv6address |  | IPv6 address. |
| islocked |  | Whether the computer is locked. |
| lastreporttime |  | Timestamp of the computer's last report. |
| locationbyiprange |  | Location derived from the IP range. |
| loggedonuser |  | Currently logged-on username. |
| macaddress |  | MAC address. |
| os |  | Operating system information. |
| providername |  | Infrastructure provider name. |
| ram |  | Installed memory. |
| relay |  | Assigned BigFix relay. |
| remotedesktopisenabled |  | Whether remote desktop is enabled. |
| subnetaddress |  | Subnet address. |
| totalsizeofsystemdrive |  | Total size of the system drive. |
| username |  | Reported username. |

#### Relationships

- `(:Device)-[:OBSERVED_AS]->(:BigfixComputer)`

- `(:BigfixRoot)-[:RESOURCE]->(:BigfixComputer)`: The BigFix root contains the computer.

### BigfixRoot

A BigFix root server containing managed computers.

#### Properties

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | BigFix root URL. |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |

#### Relationships

- `(:BigfixRoot)-[:RESOURCE]->(:BigfixComputer)`: The BigFix root contains the computer.
