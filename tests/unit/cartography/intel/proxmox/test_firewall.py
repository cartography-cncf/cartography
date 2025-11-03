"""
Tests for Proxmox firewall module.
"""
import pytest

from cartography.intel.proxmox.firewall import transform_firewall_rule_data
from cartography.intel.proxmox.firewall import transform_ipset_data


def test_transform_firewall_rule_data():
    """Test firewall rule data transformation."""
    raw_rules = [
        {
            'pos': 0,
            'type': 'in',
            'action': 'ACCEPT',
            'enable': 1,
            'proto': 'tcp',
            'dport': '22',
            'source': '10.0.0.0/8',
            'comment': 'Allow SSH',
        },
        {
            'pos': 1,
            'type': 'in',
            'action': 'DROP',
            'enable': 0,
            'comment': 'Drop disabled',
        },
    ]

    cluster_id = 'test-cluster'
    
    # Test cluster-scoped rules
    result = transform_firewall_rule_data(raw_rules, cluster_id, 'cluster')
    
    assert len(result) == 2
    
    # Test first rule
    rule1 = result[0]
    assert rule1['id'] == 'cluster:0'
    assert rule1['scope'] == 'cluster'
    assert rule1['scope_id'] is None
    assert rule1['pos'] == 0
    assert rule1['type'] == 'in'
    assert rule1['action'] == 'ACCEPT'
    assert rule1['enable'] is True
    assert rule1['proto'] == 'tcp'
    assert rule1['dport'] == '22'
    assert rule1['source'] == '10.0.0.0/8'
    assert rule1['comment'] == 'Allow SSH'
    
    # Test second rule
    rule2 = result[1]
    assert rule2['id'] == 'cluster:1'
    assert rule2['enable'] is False
    assert rule2['action'] == 'DROP'
    
    # Test node-scoped rules
    result_node = transform_firewall_rule_data(raw_rules, cluster_id, 'node', 'node1')
    
    rule_node = result_node[0]
    assert rule_node['id'] == 'node:node1:0'
    assert rule_node['scope'] == 'node'
    assert rule_node['scope_id'] == 'node1'


def test_transform_ipset_data():
    """Test IP set data transformation."""
    raw_ipsets = [
        {
            'name': 'management-ips',
            'comment': 'Management network',
        },
        {
            'name': 'backup-servers',
        },
    ]
    
    ipset_cidrs = {
        'management-ips': [
            {'cidr': '10.0.1.0/24'},
            {'cidr': '10.0.2.0/24'},
        ],
        'backup-servers': [
            {'cidr': '192.168.10.5/32'},
        ],
    }
    
    cluster_id = 'test-cluster'
    
    # Test cluster-scoped IP sets
    result = transform_ipset_data(raw_ipsets, ipset_cidrs, cluster_id, 'cluster')
    
    assert len(result) == 2
    
    # Test management-ips
    mgmt = next(s for s in result if s['name'] == 'management-ips')
    assert mgmt['id'] == 'cluster:management-ips'
    assert mgmt['scope'] == 'cluster'
    assert mgmt['scope_id'] is None
    assert mgmt['comment'] == 'Management network'
    assert mgmt['cidrs'] == ['10.0.1.0/24', '10.0.2.0/24']
    assert mgmt['cluster_id'] == cluster_id
    
    # Test backup-servers
    backup = next(s for s in result if s['name'] == 'backup-servers')
    assert backup['id'] == 'cluster:backup-servers'
    assert backup['comment'] is None
    assert backup['cidrs'] == ['192.168.10.5/32']
    
    # Test node-scoped IP sets
    result_node = transform_ipset_data(raw_ipsets, ipset_cidrs, cluster_id, 'node', 'node1')
    
    ipset_node = result_node[0]
    assert ipset_node['id'] == 'node:node1:management-ips'
    assert ipset_node['scope'] == 'node'
    assert ipset_node['scope_id'] == 'node1'
