import requests
from typing import Dict, Any

GITHUB_API_URL = 'https://api.github.com'

class GitHubPullRequestClient:
    def __init__(self, token: str):
        self.token = token
        self.headers = {'Authorization': f"token {token}"}

    def _handle_rate_limit(self):
        response = requests.get(f'{GITHUB_API_URL}/rate_limit', headers=self.headers)
        response.raise_for_status()
        rate_limit_obj = response.json()['resources']['core']
        remaining = rate_limit_obj['remaining']
        if remaining == 0:
            reset_at = datetime.fromtimestamp(rate_limit_obj['reset'], tz=tz.utc)
            now = datetime.now(tz.utc)
            sleep_duration = reset_at - now + timedelta(minutes=1)
            logger.warning(
                f'GitHub API rate limit has {remaining} remaining, sleeping until reset at {reset_at} for {sleep_duration}',
            )
            time.sleep(sleep_duration.seconds)

    def get_pull_request_data(self, repo: str, pr_id: int) -> Dict[str, Any]:
        self._handle_rate_limit()
        response = requests.get(f'{GITHUB_API_URL}/repos/{repo}/pulls/{pr_id}', headers=self.headers)
        response.raise_for_status()
        return response.json()

    def get_pull_request_comments(self, repo: str, pr_id: int) -> Dict[str, Any]:
        self._handle_rate_limit()
        response = requests.get(f'{GITHUB_API_URL}/repos/{repo}/issues/{pr_id}/comments', headers=self.headers)
        response.raise_for_status()
        return response.json()

def get_pull_request_info(token: str, repo: str, pr_id: int) -> Dict[str, Any]:
    client = GitHubPullRequestClient(token)
    pr_data = client.get_pull_request_data(repo, pr_id)
    pr_comments = client.get_pull_request_comments(repo, pr_id)
    return {
        'pull_request': pr_data,
        'comments': pr_comments
    }

if __name__ == '__main__':
    import os
    import json

    token = os.getenv('GITHUB_TOKEN')
    repo = 'OWNER/REPO'  # Replace with the actual repository
    pr_id = 1  # Replace with the actual pull request ID

    pr_info = get_pull_request_info(token, repo, pr_id)
    print(json.dumps(pr_info, indent=4))