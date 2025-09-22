import requests
from typing import Optional, List

def post_slack_webhook(webhook_url: str, text: str, blocks: Optional[list] = None):
    if not webhook_url:
        return False, "No webhook URL configured"
    payload = {
        "text": text,
    }
    if blocks:
        payload["blocks"] = blocks
    resp = requests.post(webhook_url, json=payload, timeout=15)
    ok = (200 <= resp.status_code < 300)
    return ok, None if ok else f"HTTP {resp.status_code}: {resp.text[:200]}"

def render_failure_blocks(alert_prefix: str, mention: str, repo_full: str, branch: str, workflow_name: str, conclusion: str, duration: str, url: str, snippet: str = "") -> list:
    mention_tag = f"<!{mention}> " if mention else ""
    title = f"{alert_prefix} {repo_full} / {branch} → {workflow_name} FAILED"
    blocks = [
        {"type":"section","text":{"type":"mrkdwn","text": f"{mention_tag}*{title}*"}},
        {"type":"section","text":{"type":"mrkdwn","text": f"*Conclusion:* `{conclusion}`\n*Duration:* `{duration}`\n*Run:* <{url}|Open in GitHub>"}},
    ]
    if snippet:
        blocks.append({"type":"section","text":{"type":"mrkdwn","text": f"*Log Snippet:*\n```{snippet[:2900]}```"}})
    return blocks
