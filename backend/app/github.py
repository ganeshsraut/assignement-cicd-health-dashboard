import requests
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timezone
from dateutil import parser as dtparser

API_URL = "https://api.github.com"

class GitHubClient:
    def __init__(self, token: str):
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "ci-dashboard"
        })

    def _get_paginated(self, url: str, params: Dict=None) -> List[Dict]:
        params = params or {}
        items = []
        while url:
            resp = self.session.get(url, params=params, timeout=30)
            if resp.status_code == 304:
                break
            resp.raise_for_status()
            items.extend(resp.json())
            # Parse pagination
            next_url = None
            if 'link' in resp.headers:
                links = self._parse_link_header(resp.headers['link'])
                next_url = links.get('next')
            url = next_url
            params = None  # after first request, follow the 'next' URL only
        return items

    @staticmethod
    def _parse_link_header(value: str) -> Dict[str, str]:
        # Parses GitHub Link header
        links = {}
        for part in value.split(','):
            section = part.split(';')
            if len(section) < 2:
                continue
            url = section[0].strip()[1:-1]
            rel = section[1].strip().split('=')[1].strip('"')
            links[rel] = url
        return links

    # Discover repos the user can access
    def list_all_repos(self) -> List[Dict]:
        # Use affiliation to include owner, collaborator, org member
        params = {"per_page": 100, "affiliation": "owner,collaborator,organization_member"}
        return self._get_paginated(f"{API_URL}/user/repos", params)

    def list_runs(self, owner: str, repo: str, per_page: int = 50) -> Dict:
        params = {"per_page": per_page}
        url = f"{API_URL}/repos/{owner}/{repo}/actions/runs"
        resp = self.session.get(url, params=params, timeout=30)
        if resp.status_code == 304:
            return {"workflow_runs": []}
        resp.raise_for_status()
        return resp.json()

    def list_jobs_for_run(self, owner: str, repo: str, run_id: int) -> Dict:
        url = f"{API_URL}/repos/{owner}/{repo}/actions/runs/{run_id}/jobs"
        resp = self.session.get(url, params={"per_page": 100}, timeout=60)
        resp.raise_for_status()
        return resp.json()

    def download_job_log(self, owner: str, repo: str, job_id: int) -> bytes:
        url = f"{API_URL}/repos/{owner}/{repo}/actions/jobs/{job_id}/logs"
        # GitHub may redirect to signed URL; allow redirects
        resp = self.session.get(url, allow_redirects=True, timeout=120)
        resp.raise_for_status()
        return resp.content
