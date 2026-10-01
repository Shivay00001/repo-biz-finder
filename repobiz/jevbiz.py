"""Business-potential scoring via Jev (TypeSafe System One).

Standing rule: decisions go through Jev, not gut calls. For each candidate
repo we ask Jev:
  - noul 'productizable': P(this repo can become a sellable software-product
    business with reasonable effort by a solo developer)
  - choice 'model': best monetization model for it.
"""

import json
import subprocess
from pathlib import Path

JEV_PY = Path.home() / "workspace/skills/typesafe/bin/jev.py"

MONETIZATION = {
    "hosted_saas": "Hosted SaaS: run it for customers, charge monthly subscription.",
    "white_label": "White-label: rebrand and resell to agencies/businesses.",
    "managed_service": "Managed service: set up + maintain it for clients, charge setup + retainer.",
    "onetime_product": "One-time product: packaged download/template with paid updates.",
    "plugin_extension": "Plugin/extension/add-on sold on a marketplace.",
}


def jev_score_repo(repo, fast_cash=False):
    state = {
        "repo": repo["full_name"],
        "description": (repo.get("description") or "")[:300],
        "stars": repo.get("stargazers_count", 0),
        "language": repo.get("language"),
        "license": (repo.get("license") or {}).get("spdx_id"),
        "topics": (repo.get("topics") or [])[:8],
        "open_issues": repo.get("open_issues_count", 0),
    }
    questions = {
        "productizable": {
            "type": "noul",
            "instructions": (
                "You are evaluating an open-source GitHub repository as a raw "
                "material for a solo developer's software-product business. "
                "Consider: does it solve a real painful problem for businesses "
                "or developers? Is it the kind of thing people pay for (hosting, "
                "convenience, white-label, done-for-you)? Is the scope small enough "
                "for one person to productize in weeks, not years? "
                "Answer yes if this repo can realistically become a sellable "
                "software product business with reasonable effort."
            ),
        },
        "model": {
            "type": "choice",
            "instructions": (
                "Pick the single best monetization model for turning this "
                "open-source repo into a revenue-generating business."
            ),
            "criteria": MONETIZATION,
        },
    }
    if fast_cash:
        questions["fast_cash"] = {
            "type": "noul",
            "instructions": (
                "Same repo, same solo developer with zero budget. Answer yes if "
                "this could realistically generate its FIRST revenue within 60 "
                "days of focused work — i.e. the product is close to sellable, "
                "the buyers are easy to reach, and no long R&D or heavy "
                "infrastructure is needed first."
            ),
        }
    payload = {"model": "jev-latest", "state": state, "questions": questions}
    proc = subprocess.run(
        ["python3", str(JEV_PY)],
        input=json.dumps(payload),
        capture_output=True, text=True, timeout=180,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"Jev call failed: {(proc.stderr or proc.stdout)[:300]}")
    out = json.loads(proc.stdout)
    answers = out.get("answers", {})
    prod = answers.get("productizable", {}) or {}
    model = answers.get("model", {}) or {}
    # noul shape: {"type": "noul", "noul": 0.54}
    prob = prod.get("noul", prod.get("probability", prod.get("p", 0)))
    if isinstance(prob, dict):
        prob = prob.get("yes", 0)
    # choice shape: {"type": "choice", "choice": "hosted_saas",
    #                "probabilities": {...}, "confidence": 0.58}
    fast = answers.get("fast_cash", {}) or {}
    fast_p = fast.get("noul", fast.get("probability", fast.get("p", 0)))
    if isinstance(fast_p, dict):
        fast_p = fast_p.get("yes", 0)
    return {
        "productizable_p": round(float(prob or 0), 3),
        "fast_cash_p": round(float(fast_p or 0), 3),
        "model": model.get("choice") or model.get("value"),
        "model_dist": model.get("probabilities") or model.get("distribution", {}),
        "model_confidence": model.get("confidence"),
        "raw": out,
    }
