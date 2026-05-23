"""Deployment adapters: GitHub repo + Vercel."""
from __future__ import annotations

import base64
from typing import Any

import httpx

from helix.core.config import get_settings
from helix.tools.base import Tool, ToolResult


class GithubRepoTool(Tool):
    name = "github_repo"
    description = "Create a GitHub repo and push files via the REST API."

    async def _call(
        self,
        *,
        repo_name: str,
        files: dict[str, str],
        owner: str | None = None,
        description: str = "",
        private: bool = True,
        commit_message: str = "Initial commit from Helix",
        **_: Any,
    ) -> ToolResult:
        settings = get_settings()
        if not settings.github_token:
            return ToolResult(ok=False, error="GITHUB_TOKEN not configured")
        headers = {
            "Authorization": f"Bearer {settings.github_token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        async with httpx.AsyncClient(timeout=60, headers=headers) as http:
            # Determine owner
            owner_login = owner
            if not owner_login:
                me = await http.get("https://api.github.com/user")
                me.raise_for_status()
                owner_login = me.json()["login"]

            # Create repo (idempotent: 422 means exists)
            create_url = "https://api.github.com/user/repos"
            create_resp = await http.post(
                create_url,
                json={
                    "name": repo_name,
                    "description": description,
                    "private": private,
                    "auto_init": True,
                },
            )
            if create_resp.status_code not in (201, 422):
                return ToolResult(
                    ok=False,
                    error=f"github create_repo failed: {create_resp.status_code} {create_resp.text}",
                )

            api_repo = f"https://api.github.com/repos/{owner_login}/{repo_name}"

            # Get default branch
            repo_meta = await http.get(api_repo)
            repo_meta.raise_for_status()
            default_branch = repo_meta.json().get("default_branch", "main")

            # Write each file via contents API
            for path, content in files.items():
                b64 = base64.b64encode(content.encode("utf-8")).decode("utf-8")
                contents_url = f"{api_repo}/contents/{path}"
                # See if file exists to get sha
                existing = await http.get(contents_url, params={"ref": default_branch})
                payload: dict[str, Any] = {
                    "message": commit_message,
                    "content": b64,
                    "branch": default_branch,
                }
                if existing.status_code == 200:
                    payload["sha"] = existing.json()["sha"]
                put_resp = await http.put(contents_url, json=payload)
                if put_resp.status_code not in (200, 201):
                    return ToolResult(
                        ok=False,
                        error=f"github put {path} failed: {put_resp.status_code} {put_resp.text}",
                    )

            return ToolResult(
                ok=True,
                data={
                    "owner": owner_login,
                    "repo": repo_name,
                    "url": f"https://github.com/{owner_login}/{repo_name}",
                    "default_branch": default_branch,
                    "files": list(files.keys()),
                },
            )


class VercelDeployTool(Tool):
    name = "vercel_deploy"
    description = "Trigger a Vercel deployment for a GitHub repo via REST API."

    async def _call(
        self,
        *,
        project_name: str,
        github_repo: str,  # "owner/repo"
        framework: str = "nextjs",
        team_id: str | None = None,
        **_: Any,
    ) -> ToolResult:
        settings = get_settings()
        if not settings.vercel_token:
            return ToolResult(ok=False, error="VERCEL_TOKEN not configured")
        headers = {
            "Authorization": f"Bearer {settings.vercel_token}",
            "Content-Type": "application/json",
        }
        params = {"teamId": team_id} if team_id else {}
        async with httpx.AsyncClient(timeout=120, headers=headers) as http:
            # Create project linked to repo
            proj_resp = await http.post(
                "https://api.vercel.com/v10/projects",
                params=params,
                json={
                    "name": project_name,
                    "framework": framework,
                    "gitRepository": {"type": "github", "repo": github_repo},
                },
            )
            if proj_resp.status_code not in (200, 201, 409):
                return ToolResult(
                    ok=False,
                    error=f"vercel create_project failed: {proj_resp.status_code} {proj_resp.text}",
                )

            # Trigger a deployment
            owner, repo = github_repo.split("/", 1)
            deploy_resp = await http.post(
                "https://api.vercel.com/v13/deployments",
                params=params,
                json={
                    "name": project_name,
                    "gitSource": {
                        "type": "github",
                        "repo": repo,
                        "ref": "main",
                        "org": owner,
                    },
                    "target": "production",
                },
            )
            if deploy_resp.status_code not in (200, 201):
                return ToolResult(
                    ok=False,
                    error=f"vercel deploy failed: {deploy_resp.status_code} {deploy_resp.text}",
                )
            body = deploy_resp.json()
            return ToolResult(
                ok=True,
                data={
                    "deployment_id": body.get("id"),
                    "url": f"https://{body.get('url')}" if body.get("url") else None,
                    "status": body.get("readyState") or body.get("status"),
                    "project": project_name,
                    "repo": github_repo,
                },
            )
