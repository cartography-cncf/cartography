from cartography.rules.data.frameworks.iso27001 import iso27001_annex_a
from cartography.rules.data.frameworks.soc2 import soc2_tsc
from cartography.rules.spec.model import Fact
from cartography.rules.spec.model import Finding
from cartography.rules.spec.model import Maturity
from cartography.rules.spec.model import Module
from cartography.rules.spec.model import Rule

_GITHUB_FNMATCH_REPLACEMENTS = """
[
    ['.', '[.]'],
    ['+', '[+]'],
    ['(', '[(]'],
    [')', '[)]'],
    ['{', '[{]'],
    ['}', '[}]'],
    ['$', '[$]'],
    ['|', '[|]'],
    ['[!', '[^'],
    ['**/', '<GLOBSTAR_SLASH>'],
    ['**', '<GLOBSTAR>'],
    ['*', '[^/]*'],
    ['?', '[^/]'],
    ['<GLOBSTAR_SLASH>', '(?:.*/)?'],
    ['<GLOBSTAR>', '.*']
]
"""


class GitHubRepositoryWithoutRequiredReviewsOutput(Finding):
    repository: str | None = None
    repository_id: str | None = None
    default_branch: str | None = None


_github_repository_without_required_reviews = Fact(
    id="github_repository_without_required_reviews",
    name="GitHub repositories without mandatory pull request reviews",
    description=(
        "Detects active GitHub repositories that have no branch protection rule "
        "requiring at least one approving pull request review."
    ),
    cypher_query="""
    MATCH (repo:GitHubRepository)
    WHERE coalesce(repo.archived, false) = false
      AND coalesce(repo.disabled, false) = false
      AND NOT (
        EXISTS {
            MATCH (repo)-[:HAS_RULE]->(rule:GitHubBranchProtectionRule)
            WHERE repo.defaultbranch =~ (
                '^'
                + reduce(
                    regex = rule.pattern,
                    replacement IN
    """
    + _GITHUB_FNMATCH_REPLACEMENTS
    + """
                    | replace(regex, replacement[0], replacement[1])
                )
                + '$'
              )
              AND coalesce(rule.requires_approving_reviews, false) = true
              AND coalesce(rule.required_approving_review_count, 0) >= 1
        }
        OR EXISTS {
            MATCH (repo)-[:HAS_RULESET]->(ruleset:GitHubRuleset)
                  -[:CONTAINS_RULE]->(rule:GitHubRulesetRule)
            WHERE ruleset.target = 'BRANCH'
              AND ruleset.enforcement = 'ACTIVE'
              AND rule.type = 'PULL_REQUEST'
              AND coalesce(rule.parameters_required_approving_review_count, 0) >= 1
              AND any(
                pattern IN coalesce(ruleset.conditions_ref_name_include, [])
                WHERE pattern IN ['~ALL', '~DEFAULT_BRANCH']
                   OR ('refs/heads/' + repo.defaultbranch) =~ (
                        '^'
                        + reduce(
                            regex = pattern,
                            replacement IN
    """
    + _GITHUB_FNMATCH_REPLACEMENTS
    + """
                            | replace(regex, replacement[0], replacement[1])
                        )
                        + '$'
                   )
              )
              AND none(
                pattern IN coalesce(ruleset.conditions_ref_name_exclude, [])
                WHERE pattern IN ['~ALL', '~DEFAULT_BRANCH']
                   OR ('refs/heads/' + repo.defaultbranch) =~ (
                        '^'
                        + reduce(
                            regex = pattern,
                            replacement IN
    """
    + _GITHUB_FNMATCH_REPLACEMENTS
    + """
                            | replace(regex, replacement[0], replacement[1])
                        )
                        + '$'
                   )
              )
        }
      )
    RETURN
        repo.fullname AS repository,
        repo.id AS repository_id,
        repo.defaultbranch AS default_branch
    """,
    cypher_visual_query="""
    MATCH (repo:GitHubRepository)
    WHERE coalesce(repo.archived, false) = false
      AND coalesce(repo.disabled, false) = false
      AND NOT (
        EXISTS {
            MATCH (repo)-[:HAS_RULE]->(rule:GitHubBranchProtectionRule)
            WHERE repo.defaultbranch =~ (
                '^'
                + reduce(
                    regex = rule.pattern,
                    replacement IN
    """
    + _GITHUB_FNMATCH_REPLACEMENTS
    + """
                    | replace(regex, replacement[0], replacement[1])
                )
                + '$'
              )
              AND coalesce(rule.requires_approving_reviews, false) = true
              AND coalesce(rule.required_approving_review_count, 0) >= 1
        }
        OR EXISTS {
            MATCH (repo)-[:HAS_RULESET]->(ruleset:GitHubRuleset)
                  -[:CONTAINS_RULE]->(rule:GitHubRulesetRule)
            WHERE ruleset.target = 'BRANCH'
              AND ruleset.enforcement = 'ACTIVE'
              AND rule.type = 'PULL_REQUEST'
              AND coalesce(rule.parameters_required_approving_review_count, 0) >= 1
              AND any(
                pattern IN coalesce(ruleset.conditions_ref_name_include, [])
                WHERE pattern IN ['~ALL', '~DEFAULT_BRANCH']
                   OR ('refs/heads/' + repo.defaultbranch) =~ (
                        '^'
                        + reduce(
                            regex = pattern,
                            replacement IN
    """
    + _GITHUB_FNMATCH_REPLACEMENTS
    + """
                            | replace(regex, replacement[0], replacement[1])
                        )
                        + '$'
                   )
              )
              AND none(
                pattern IN coalesce(ruleset.conditions_ref_name_exclude, [])
                WHERE pattern IN ['~ALL', '~DEFAULT_BRANCH']
                   OR ('refs/heads/' + repo.defaultbranch) =~ (
                        '^'
                        + reduce(
                            regex = pattern,
                            replacement IN
    """
    + _GITHUB_FNMATCH_REPLACEMENTS
    + """
                            | replace(regex, replacement[0], replacement[1])
                        )
                        + '$'
                   )
              )
        }
      )
    RETURN repo
    """,
    cypher_count_query="""
    MATCH (repo:GitHubRepository)
    WHERE coalesce(repo.archived, false) = false
      AND coalesce(repo.disabled, false) = false
    RETURN COUNT(repo) AS count
    """,
    asset_label="GitHubRepository",
    asset_id_field="repository_id",
    identity_fields=("repository_id",),
    module=Module.GITHUB,
    maturity=Maturity.EXPERIMENTAL,
)


github_repositories_without_required_reviews = Rule(
    id="github_repositories_without_required_reviews",
    name="GitHub Repositories Without Mandatory Reviews",
    description=(
        "Detects active repositories that do not enforce at least one approving "
        "pull request review through branch protection or rulesets."
    ),
    output_model=GitHubRepositoryWithoutRequiredReviewsOutput,
    facts=(_github_repository_without_required_reviews,),
    tags=("github", "change_management", "code_review", "compliance"),
    version="0.1.0",
    frameworks=(
        iso27001_annex_a("8.32"),
        soc2_tsc("CC8.1"),
    ),
)
