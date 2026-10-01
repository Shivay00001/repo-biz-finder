"""Clone + business-brief generation."""

import subprocess
from datetime import datetime
from pathlib import Path


def shallow_clone(clone_url, dest_dir, timeout=300):
    dest = Path(dest_dir)
    if dest.exists():
        return str(dest), False  # already cloned
    dest.parent.mkdir(parents=True, exist_ok=True)
    proc = subprocess.run(
        ["git", "clone", "--depth", "1", clone_url, str(dest)],
        capture_output=True, text=True, timeout=timeout,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"git clone failed: {(proc.stderr or '')[:300]}")
    return str(dest), True


def license_notice_text(repo, verdict, obligation):
    lic = repo.get("license") or {}
    return (
        f"License: {lic.get('name') or 'unknown'} ({lic.get('spdx_id') or 'no SPDX'})\n"
        f"Verdict: {verdict}\n"
        f"Obligation: {obligation}\n"
    )


def write_brief(dest_dir, repo, verdict, obligation, qscore, qparts,
                jev, has_ci, readme_snippet):
    full = repo["full_name"]
    model_desc = {
        "hosted_saas": "Hosted SaaS — run it for customers, monthly subscription",
        "white_label": "White-label — rebrand and resell to agencies/businesses",
        "managed_service": "Managed service — setup + retainer for clients",
        "onetime_product": "One-time product — packaged download with paid updates",
        "plugin_extension": "Plugin/extension sold on a marketplace",
    }.get(jev.get("model"), jev.get("model"))

    brief = f"""# Business Brief — {full}

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}
Repo: https://github.com/{full}

## What it is
{(repo.get('description') or 'No description.')}

Language: {repo.get('language')} | Stars: {repo.get('stargazers_count')} | Forks: {repo.get('forks_count')} | Open issues: {repo.get('open_issues_count')}
Quality score: {qscore}/100 (popularity {qparts.get('popularity', 0):.0f}, maintenance {qparts.get('maintenance', 0):.0f}, health {qparts.get('health', 0):.0f}, completeness {qparts.get('completeness', 0):.0f})
CI workflows present: {'yes' if has_ci else 'not detected'} | Last push: {qparts.get('days_since_push')} days ago

## License check
{license_notice_text(repo, verdict, obligation)}
Keep a `THIRD_PARTY_LICENSES.md` in the product with the original copyright
notice and license text. This is mandatory for MIT/Apache/BSD.

## Jev business verdict
Productizable probability: {jev.get('productizable_p')}
Recommended model: {model_desc}

## Productization plan
1. Clone is at `clones/{full.replace('/', '__')}/` — read the README and get it running locally first.
2. Identify the painful job it does for a business user; wrap that as the headline offer.
3. Productize per the model above:
   - hosted_saas → deploy multi-tenant, add auth + billing (Stripe), pricing page.
   - white_label → rebrand UI, per-client config, sell to agencies.
   - managed_service → offer setup + monthly care plan (fits VisionQuantech's existing rate card).
   - onetime_product → package, docs, Gumroad listing.
   - plugin_extension → marketplace listing (e.g. VS Code, WordPress, Shopify).
4. Add the license attribution file before any distribution.

## README excerpt
```
{readme_snippet[:1500]}
```
"""
    path = Path(dest_dir) / "BUSINESS_BRIEF.md"
    path.write_text(brief, encoding="utf-8")
    return str(path)
