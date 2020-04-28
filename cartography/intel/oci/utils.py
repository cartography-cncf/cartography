#Copyright (c) 2020, Oracle and/or its affiliates.
# OCI intel module - utility functions
import json

#Generic way to turn a OCI ptyhon object into the json response that you would see from calling the REST API.
def oci_object_to_json(obj):
    list=[]
    for dict in json.loads(str(obj)):
        list.append(replace_char_in_dict(dict))
    return list

#Have to replace _ with - in dictionary keys, since _ is subsititued for - in OCI object variables.
def replace_char_in_dict(d):
    new = {}
    for k, v in d.items():
        if isinstance(v, dict):
            v = replace_char_in_dict(v)
        new[k.replace('_', '-')] = v
    return new

# Grab list of all compartments and sub-compartments in neo4j already populated by iam.
def get_compartments_in_tenancy(neo4j_session, tenancy_id):
    query = "MATCH (OCITenancy{ocid: {OCI_TENANCY_ID}})-[*]->(compartment:OCICompartment) " \
            "return DISTINCT compartment.name as name, compartment.ocid as ocid, compartment.compartmentid as compartmentid;"
    return neo4j_session.run(query, OCI_TENANCY_ID=tenancy_id)

# Grab list of all groups in neo4j already populated by iam.
def get_groups_in_tenancy(neo4j_session, tenancy_id):
    query = "MATCH (OCITenancy{ocid: {OCI_TENANCY_ID}})-[*]->(group:OCIGroup)" \
            "return DISTINCT group.name as name, group.ocid as ocid;"
    return neo4j_session.run(query, OCI_TENANCY_ID=tenancy_id)

# Grab list of all policies in neo4j already populated by iam.
def get_policies_in_tenancy(neo4j_session, tenancy_id):
    query = "MATCH (OCITenancy{ocid: {OCI_TENANCY_ID}})-[*]->(policy:OCIPolicy)" \
            "return DISTINCT policy.name as name, policy.ocid as ocid, policy.statements as statements, policy.compartmentid as compartmentid;"
    return neo4j_session.run(query, OCI_TENANCY_ID=tenancy_id)

# Grab list of all regions in neo4j already populated by iam.
def get_regions_in_tenancy(neo4j_session, tenancy_id):
    query = "MATCH (OCITenancy{ocid: {OCI_TENANCY_ID}})-->(region:OCIRegion)" \
            "return DISTINCT region.name as name, region.key as key;"
    return neo4j_session.run(query, OCI_TENANCY_ID=tenancy_id)

# Grab list of all security groups in neo4j already populated by network. Need to handle regions for this one.
def get_security_groups_in_tenancy(neo4j_session, tenancy_id, region):
    query = "MATCH (OCITenancy{ocid: {OCI_TENANCY_ID}})-[*]->(security_group:OCINetworkSecurityGroup)-[OCI_REGION]->(region:OCIRegion{name: {OCI_REGION}})" \
            "return DISTINCT security_group.name as name, security_group.ocid as ocid, security_group.compartmentid as compartmentid;"
    return neo4j_session.run(query, OCI_TENANCY_ID=tenancy_id, OCI_REGION=region)