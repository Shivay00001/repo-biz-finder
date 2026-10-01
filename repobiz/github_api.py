"""GitHub API wrapper via the stored custom.github credential (surrogate auth).

All calls go through ~/workspace/skills/github/bin/gh.py so no raw
credential ever touches this code. Never print or log surrogate values.
"""

import json
import subprocess
import urllib.parse
from pathlib import Path

GH_PY = Path.home() / "workspace/skills/github/bin/gh.py"


def api(method, path, body=None, timeout=60):
    cmd = ["python3", str(GH_PY), method, path]
    if body is not None:
        cmd.append(json.dumps(body))
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    if proc.returncode != 0:
        err = (proc.stderr or proc.stdout or "").strip()
        raise RuntimeError(f"GitHub API {method} {path} failed: {err[:300]}")
    try:
        envelope = json.loads(proc.stdout) if proc.stdout.strip() else {}
    except json.JSONDecodeError:
        raise RuntimeError(f"GitHub API {method} {path} returned non-JSON output")
    # gh.py wraps: {"http_status": 200, "body": {...}}
    if isinstance(envelope, dict) and "http_status" in envelope:
        if envelope["http_status"] >= 400:
            raise RuntimeError(
                f"GitHub API {method} {path} HTTP {envelope['http_status']}: "
                f"{json.dumps(envelope.get('body', {}))[:300]}"
            )
        return envelope.get("body", {})
    return envelope


def search_repos(query, per_page=30, page=1, sort="stars", order="desc"):
    q = urllib.parse.quote_plus(query)
    path = (f"/search/repositories?q={q}&per_page={per_page}"
            f"&page={page}&sort={sort}&order={order}")
    return api("GET", path)


def repo_full_name(owner, repo):
    return api("GET", f"/repos/{owner}/{repo}")


def has_ci_workflows(owner, repo):
    """True if the repo has GitHub Actions workflows (signal of tested, working code)."""
    try:
        data = api("GET", f"/repos/{owner}/{repo}/contents/.github/workflows")
        return isinstance(data, list) and len(data) > 0
    except RuntimeError:
        return False


def readme_text(owner, repo, max_chars=4000):
    """Fetch README (used for the business brief). Returns '' on failure."""
    try:
        data = api("GET", f"/repos/{owner}/{repo}/readme",
                   timeout=30)
        import base64
        content = data.get("content", "")
        text = base64.b64decode(content).decode("utf-8", errors="replace")
        return text[:max_chars]
    except Exception:
        return ""
