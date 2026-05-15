from cartography.util import run_cleanup_job
from cartography.util import timeit


@timeit
def run(neo4j_session, config):
    common_job_parameters = {
        "UPDATE_TAG": config.update_tag,
        "WORKSPACE_ID": config.params['workspace']['id_string'],
        "WORKSPACE_NAME": config.params['workspace']['name'],
        "WORKSPACE_ACCOUNT_ID": config.params['workspace']['account_id'],
    }

    load_cloudanix_workspace(neo4j_session, config.update_tag, common_job_parameters)

    # TODO: do we need to cleanup?
    # run_cleanup_job('cloudanix_workspace_cleanup.json', neo4j_session, common_job_parameters)


def load_cloudanix_workspace(neo4j_session, update_tag, common_job_parameters):
    neo4j_session.execute_write(load_cloudanix_workspace_tx, update_tag, common_job_parameters)


def load_cloudanix_workspace_tx(tx, update_tag, common_job_parameters):
    # TODO: do we need to assign `account_id`, it changes for each inventory run. Is it used anywhere?
    query = """
    MERGE (w:CloudanixWorkspace{id: $WORKSPACE_ID})
    ON CREATE SET
        w.firstseen = timestamp()
    SET
        w.lastupdated = $UPDATE_TAG,
        w.name = $WORKSPACE_NAME,
        w.account_id= $WORKSPACE_ACCOUNT_ID
    """

    tx.run(
        query,
        WORKSPACE_ID=common_job_parameters['WORKSPACE_ID'],
        WORKSPACE_NAME=common_job_parameters['WORKSPACE_NAME'],
        WORKSPACE_ACCOUNT_ID=common_job_parameters['WORKSPACE_ACCOUNT_ID'],
        UPDATE_TAG=update_tag,
    )
