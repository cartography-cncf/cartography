"""gcp_resources.py
Author: Sapna Mohanta

Ingestion module that demonstrates collecting GCP metadata and writing to Neo4j.
Placeholders are used for credentials and project ids. To run locally, set the
environment variables as documented in .env.example and provide your service account.
"""

import os
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build
from neo4j import GraphDatabase

# Read configuration from environment (placeholders used in repo)
NEO4J_URI = os.environ.get('NEO4J_URI', 'bolt://localhost:7687')
NEO4J_USER = os.environ.get('NEO4J_USER', 'neo4j')
NEO4J_PASSWORD = os.environ.get('NEO4J_PASSWORD', 'changeme')
GCP_PROJECT = os.environ.get('GCP_PROJECT_ID', 'my-gcp-project-id')
SERVICE_ACCOUNT = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS', 'gcp-key.json')

def get_credentials():
    return service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT)

def list_instances(project_id):
    credentials = get_credentials()
    service = build('compute', 'v1', credentials=credentials)
    request = service.instances().aggregatedList(project=project_id)
    items = []
    while request is not None:
        resp = request.execute()
        for zone, data in resp.get('items', {}).items():
            for inst in data.get('instances', []):
                items.append({
                    'instance_id': inst.get('id'),
                    'name': inst.get('name'),
                    'zone': zone,
                    'status': inst.get('status')
                })
        request = service.instances().aggregatedList_next(previous_request=request, previous_response=resp)
    return items

def list_buckets(project_id):
    credentials = get_credentials()
    service = build('storage', 'v1', credentials=credentials)
    req = service.buckets().list(project=project_id)
    out = []
    while req is not None:
        resp = req.execute()
        for b in resp.get('items', []):
            out.append({'name': b.get('name'), 'location': b.get('location'), 'storageClass': b.get('storageClass')})
        req = service.buckets().list_next(previous_request=req, previous_response=resp)
    return out

def write_to_neo4j(instances, buckets):
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    with driver.session() as session:
        for i in instances:
            session.run("""MERGE (p:GCPProject {id: $project})
                          MERGE (n:GCPInstance {id: $id})
                          SET n.name = $name, n.zone = $zone, n.status = $status
                          MERGE (p)-[:HAS_INSTANCE]->(n)
                       """, project=GCP_PROJECT, id=str(i['instance_id']), name=i['name'], zone=i['zone'], status=i['status'])
        for b in buckets:
            session.run("""MERGE (p:GCPProject {id: $project})
                          MERGE (b:GCPBucket {name: $name})
                          SET b.location = $location, b.storageClass = $storageClass
                          MERGE (p)-[:HAS_BUCKET]->(b)
                       """, project=GCP_PROJECT, name=b['name'], location=b['location'], storageClass=b['storageClass'])

def main():
    print('Starting ingestion (placeholders used).')
    instances = []
    buckets = []
    try:
        instances = list_instances(GCP_PROJECT)
    except Exception as e:
        print('Instances: could not fetch (needs valid creds):', e)
    try:
        buckets = list_buckets(GCP_PROJECT)
    except Exception as e:
        print('Buckets: could not fetch (needs valid creds):', e)

    # write_to_neo4j will attempt to connect to Neo4j if available
    try:
        write_to_neo4j(instances, buckets)
        print('Ingestion to Neo4j complete (if Neo4j was reachable).')
    except Exception as e:
        print('Neo4j write failed (placeholder credentials?):', e)

if __name__ == '__main__':
    main()
