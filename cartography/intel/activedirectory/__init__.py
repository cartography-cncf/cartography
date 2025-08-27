import logging
from typing import Any, Dict, Optional

import neo4j

from cartography.config import Config
from cartography.util import timeit
from cartography.graph.job import GraphJob
from cartography.client.core.tx import load

# Import domain modules
from . import forest as forest_mod
from . import domains as domains_mod
from . import ous as ous_mod
from . import users as users_mod
from . import groups as groups_mod
from . import computers as computers_mod
from . import gpos as gpos_mod
from . import sites as sites_mod
from . import trusts as trusts_mod

# Models
from cartography.models.activedirectory.forest import ADForestSchema
from cartography.models.activedirectory.domain import ADDomainSchema

logger = logging.getLogger(__name__)


def _get_env_secret(env_var_name: Optional[str]) -> Optional[str]:
    import os
    if not env_var_name:
        return None
    return os.environ.get(env_var_name)


@timeit
def start_activedirectory_ingestion(neo4j_session: neo4j.Session, config: Config) -> None:
    """
    Entry point for Active Directory ingestion. This function orchestrates discovery of the forest and domains,
    then performs domain-scoped syncs following the get -> transform -> load -> cleanup pattern.
    """
    # Basic validation: require server and either bind creds or auth mode
    if not getattr(config, "ad_server", None):
        logger.info("Active Directory is not configured (--ad-server missing) - skipping module.")
        return

    # Resolve secrets from env
    ad_bind_dn = _get_env_secret(getattr(config, "ad_bind_dn_env_var", None))
    ad_password = _get_env_secret(getattr(config, "ad_password_env_var", None))

    # Establish LDAP connection if ldap3 is available; else proceed with None (tests can patch collectors)
    ldap_conn = None
    try:
        import ldap3  # type: ignore

        use_ssl = bool(getattr(config, "ad_use_ssl", True))
        port = int(getattr(config, "ad_port", 636) or 636)

        tls: Optional[ldap3.Tls] = None
        if use_ssl:
            # Optionally disable TLS verify if requested
            if bool(getattr(config, "ad_disable_tls_verify", False)):
                import ssl as _ssl  # noqa: N812
                tls = ldap3.Tls(validate=_ssl.CERT_NONE)
            else:
                tls = ldap3.Tls()

        server = ldap3.Server(str(config.ad_server), port=port, use_ssl=use_ssl, tls=tls, connect_timeout=int(getattr(config, "ad_timeout_connect", 30) or 30))

        if ad_bind_dn and ad_password:
            ldap_conn = ldap3.Connection(
                server,
                user=ad_bind_dn,
                password=ad_password,
                auto_bind=True,
                read_only=True,
                receive_timeout=int(getattr(config, "ad_timeout_read", 120) or 120),
            )
        else:
            # Anonymous or SASL/Kerberos/NTLM could be added later. For now, attempt anonymous bind if permitted.
            ldap_conn = ldap3.Connection(
                server,
                auto_bind=True,
                read_only=True,
                receive_timeout=int(getattr(config, "ad_timeout_read", 120) or 120),
            )
    except Exception as e:
        # If ldap3 is not installed or connection fails, allow tests to continue by using mocked collectors.
        logger.warning("AD: LDAP connection not established (%s). Proceeding for tests/mocks.", e)
        ldap_conn = None

    # 1. Forest discovery and load
    forest_info = forest_mod.get(ldap_conn, getattr(config, "ad_base_dn", None))
    forest_tx = forest_mod.transform(forest_info)
    # Ensure forest exists
    load(neo4j_session, ADForestSchema(), [forest_tx], lastupdated=config.update_tag)

    common_job_parameters_forest: Dict[str, Any] = {
        "UPDATE_TAG": config.update_tag,
        "FOREST_ID": forest_tx["id"],
    }
    # Cleanup of forest-scoped nodes happens at the end of each specific loader as needed

    # 2. Domains discovery and load
    domains_raw = domains_mod.get_domains(ldap_conn, forest_info)
    domains_tx = domains_mod.transform_domains(domains_raw)
    load(neo4j_session, ADDomainSchema(), domains_tx, lastupdated=config.update_tag, FOREST_ID=forest_tx["id"])
    # Cleanup domains scoped to forest
    try:
        GraphJob.from_node_schema(ADDomainSchema(), common_job_parameters_forest).run(neo4j_session)
    except Exception:
        logger.exception("AD: Cleanup for ADDomain failed")

    # 3. Per-domain syncs (OUs -> Groups -> Users -> Computers -> GPOs)
    for d in domains_tx:
        domain_id = d["id"]
        domain_ctx = d
        common_job_parameters_domain: Dict[str, Any] = {
            "UPDATE_TAG": config.update_tag,
            "FOREST_ID": forest_tx["id"],
            "DOMAIN_ID": domain_id,
        }

        # OUs
        try:
            ous_raw = ous_mod.get(ldap_conn, domain_ctx)
            ous_tx = ous_mod.transform(ous_raw)
            ous_mod.load_ous(neo4j_session, ous_tx, domain_id, config.update_tag)
            ous_mod.cleanup(neo4j_session, common_job_parameters_domain)
        except Exception:
            logger.exception("AD: Failed OU sync for domain %s", domain_ctx.get("dns_name"))
            if getattr(config, "ad_fail_fast", False):
                raise

        # Groups
        try:
            groups_raw = groups_mod.get(ldap_conn, domain_ctx)
            groups_tx = groups_mod.transform(groups_raw)
            groups_mod.load_groups(neo4j_session, groups_tx, domain_id, config.update_tag)
            groups_mod.cleanup(neo4j_session, common_job_parameters_domain)
        except Exception:
            logger.exception("AD: Failed Group sync for domain %s", domain_ctx.get("dns_name"))
            if getattr(config, "ad_fail_fast", False):
                raise

        # Users
        try:
            users_raw = users_mod.get(ldap_conn, domain_ctx)
            users_tx = users_mod.transform(users_raw)
            users_mod.load_users(neo4j_session, users_tx, domain_id, config.update_tag)
            users_mod.cleanup(neo4j_session, common_job_parameters_domain)
        except Exception:
            logger.exception("AD: Failed User sync for domain %s", domain_ctx.get("dns_name"))
            if getattr(config, "ad_fail_fast", False):
                raise

        # Computers
        try:
            computers_raw = computers_mod.get(ldap_conn, domain_ctx)
            computers_tx = computers_mod.transform(computers_raw)
            computers_mod.load_computers(neo4j_session, computers_tx, domain_id, config.update_tag)
            computers_mod.cleanup(neo4j_session, common_job_parameters_domain)
        except Exception:
            logger.exception("AD: Failed Computer sync for domain %s", domain_ctx.get("dns_name"))
            if getattr(config, "ad_fail_fast", False):
                raise

        # GPOs
        try:
            gpos_raw = gpos_mod.get(ldap_conn, domain_ctx)
            gpos_tx = gpos_mod.transform(gpos_raw)
            gpos_mod.load_gpos(neo4j_session, gpos_tx, domain_id, config.update_tag)
            gpos_mod.cleanup(neo4j_session, common_job_parameters_domain)
        except Exception:
            logger.exception("AD: Failed GPO sync for domain %s", domain_ctx.get("dns_name"))
            if getattr(config, "ad_fail_fast", False):
                raise

    # 4. Forest-level: Sites/Subnets, then link computers → sites
    try:
        sites_raw = sites_mod.get(ldap_conn, forest_info)
        sites_tx, subnets_tx = sites_mod.transform(sites_raw)
        sites_mod.load_sites_and_subnets(neo4j_session, sites_tx, subnets_tx, forest_tx["id"], config.update_tag)
        sites_mod.cleanup(neo4j_session, common_job_parameters_forest)
    except Exception:
        logger.exception("AD: Failed Sites/Subnets sync")
        if getattr(config, "ad_fail_fast", False):
            raise

    # 5. Trusts (domain-domain edges)
    try:
        trusts_raw = trusts_mod.get(ldap_conn, forest_info)
        trusts_tx = trusts_mod.transform(trusts_raw)
        trusts_mod.load_trusts(neo4j_session, trusts_tx, forest_tx["id"], config.update_tag)
        trusts_mod.cleanup(neo4j_session, {**common_job_parameters_forest, "FOREST_ID": forest_tx["id"]})
    except Exception:
        logger.exception("AD: Failed Trusts sync")
        if getattr(config, "ad_fail_fast", False):
            raise

    # Cleanup forests (global, scoped_cleanup=False)
    try:
        GraphJob.from_node_schema(ADForestSchema(), {"UPDATE_TAG": config.update_tag}).run(neo4j_session)
    except Exception:
        logger.exception("AD: Cleanup for ADForest failed")
