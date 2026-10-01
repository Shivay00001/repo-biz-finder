"""Quality scoring for candidate repos (0-100).

Signals of a 'best working' repo:
  - popularity (stars/forks, log-scaled so mega-repos don't swallow everything)
  - maintenance (recent push, not archived/disabled)
  - health (low open-issue burden relative to popularity)
  - completeness (description, homepage, topics, releases)
"""

import math
from datetime import datetime, timezone


def _days_since(iso):
    try:
        dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
        return (datetime.now(timezone.utc) - dt).days
    except Exception:
        return 9999


def quality_score(r):
    if r.get("archived") or r.get("disabled"):
        return 0, {"rejected": "archived or disabled"}

    parts = {}
    stars = r.get("stargazers_count", 0) or 0
    forks = r.get("forks_count", 0) or 0

    # Popularity: log scale, 40 pts max
    parts["popularity"] = min(40.0, 12.0 * math.log10(max(stars, 1)) + 6.0 * math.log10(max(forks, 1)))

    # Maintenance: 30 pts max, decays after 90 days of silence
    days = _days_since(r.get("pushed_at") or "")
    if days <= 30:
        parts["maintenance"] = 30.0
    elif days <= 90:
        parts["maintenance"] = 22.0
    elif days <= 180:
        parts["maintenance"] = 12.0
    elif days <= 365:
        parts["maintenance"] = 5.0
    else:
        parts["maintenance"] = 0.0

    # Health: open issues vs stars, 15 pts max
    open_issues = r.get("open_issues_count", 0) or 0
    ratio = open_issues / max(stars, 1)
    if ratio < 0.01:
        parts["health"] = 15.0
    elif ratio < 0.03:
        parts["health"] = 10.0
    elif ratio < 0.08:
        parts["health"] = 5.0
    else:
        parts["health"] = 0.0

    # Completeness: 15 pts max
    comp = 0.0
    if r.get("description"):
        comp += 5.0
    if r.get("homepage"):
        comp += 3.0
    if r.get("topics"):
        comp += 3.0
    if r.get("has_wiki") or r.get("has_pages"):
        comp += 2.0
    if r.get("language"):
        comp += 2.0
    parts["completeness"] = comp

    total = round(sum(parts.values()), 1)
    parts["days_since_push"] = days
    return total, parts
