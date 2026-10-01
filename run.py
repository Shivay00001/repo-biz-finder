#!/usr/bin/env python3
"""RepoBiz Finder — find best working repos, check licenses, clone the
permissive ones, and generate business productization briefs.

Usage:
  python3 run.py --query "self-hosted analytics" --max 30 --top 5
  python3 run.py --preset dev-tools --top 5
  python3 run.py --preset all --top 3 --dry-run   # no cloning

Pipeline per query:
  GitHub search -> license classify (SAFE only, CAUTION flagged) ->
  quality score -> Jev business scoring (top candidates) ->
  clone top N SAFE -> BUSINESS_BRIEF.md per repo -> REPORT.md
"""

import argparse
import sys
import time
import yaml
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from repobiz import github_api, license as licmod, quality, jevbiz, productize

BASE = Path(__file__).resolve().parent
CLONES = BASE / "clones"
REPORTS = BASE / "reports"


def process_repo(item, do_clone=True):
    full = item["full_name"]
    owner, name = full.split("/", 1)
    lic = item.get("license") or {}
    verdict, note = licmod.classify(lic.get("key"), lic.get("name"))
    if verdict == "BLOCKED":
        return {"full_name": full, "verdict": verdict, "note": note, "skipped": True}
    qscore, qparts = quality.quality_score(item)
    if qscore <= 0:
        return {"full_name": full, "verdict": verdict, "note": "quality 0 (archived/disabled)", "skipped": True}
    return {
        "full_name": full, "repo": item, "verdict": verdict, "note": note,
        "qscore": qscore, "qparts": qparts, "skipped": False,
    }


def run_query(query, max_items=30, top=5, dry_run=False, tag="custom"):
    print(f"\n=== Query: {query} ===")
    results = github_api.search_repos(query, per_page=min(max_items, 30))
    items = results.get("items", [])
    print(f"Search returned {len(items)} repos (total {results.get('total_count')})")

    candidates = []
    for item in items[:max_items]:
        try:
            c = process_repo(item)
        except Exception as e:
            print(f"  skip {item.get('full_name')}: {e}")
            continue
        if c.get("skipped"):
            print(f"  BLOCKED {c['full_name']}: {c['note'][:80]}")
            continue
        candidates.append(c)
        print(f"  {c['verdict']:7s} q={c['qscore']:5.1f} {c['full_name']}")

    if not candidates:
        print("No usable candidates.")
        return []

    # Jev business scoring on the best quality candidates (limit API cost/time)
    jev_pool = sorted(candidates, key=lambda c: c["qscore"], reverse=True)[:10]
    for c in jev_pool:
        try:
            c["jev"] = jevbiz.jev_score_repo(c["repo"])
            print(f"  Jev p={c['jev']['productizable_p']} model={c['jev']['model']} {c['full_name']}")
        except Exception as e:
            print(f"  Jev failed for {c['full_name']}: {e}")
            c["jev"] = {"productizable_p": 0, "model": None}
        time.sleep(1)

    ranked = sorted(
        [c for c in jev_pool if "jev" in c],
        key=lambda c: (c["jev"]["productizable_p"], c["qscore"]),
        reverse=True,
    )

    picked = []
    for c in ranked[:top]:
        owner, name = c["full_name"].split("/", 1)
        dest = CLONES / c["full_name"].replace("/", "__")
        brief_path = None
        if not dry_run:
            try:
                clone_url = c["repo"]["clone_url"]
                _, fresh = productize.shallow_clone(clone_url, dest)
                print(f"  cloned {'(fresh)' if fresh else '(exists)'} {c['full_name']}")
            except Exception as e:
                print(f"  clone FAILED {c['full_name']}: {e}")
                c["clone_error"] = str(e)
        if dest.exists():
            try:
                ci = github_api.has_ci_workflows(owner, name)
            except Exception:
                ci = False
            readme = github_api.readme_text(owner, name)
            brief_path = productize.write_brief(
                dest, c["repo"], c["verdict"], c["note"],
                c["qscore"], c["qparts"], c["jev"], ci, readme,
            )
        c["brief"] = brief_path
        picked.append(c)
    return picked


def write_report(all_picks, tag):
    REPORTS.mkdir(exist_ok=True)
    ts = datetime.now().strftime("%Y-%m-%d_%H%M")
    path = REPORTS / f"report-{tag}-{ts}.md"
    lines = [f"# RepoBiz Report — {tag}", f"Generated: {datetime.now():%Y-%m-%d %H:%M}", ""]
    for c in all_picks:
        r = c["repo"]
        lic = r.get("license") or {}
        lines += [
            f"## {c['full_name']}",
            f"- Stars: {r.get('stargazers_count')} | Language: {r.get('language')} | License: {lic.get('name')} ({c['verdict']})",
            f"- Quality: {c['qscore']}/100 | Jev productizable: {c['jev']['productizable_p']} | Model: {c['jev']['model']}",
            f"- {r.get('description') or ''}",
            f"- Brief: `{c['brief']}`" if c.get("brief") else "- Brief: not generated (dry run)",
            "",
        ]
    path.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nReport: {path}")
    return str(path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--query", help="GitHub search query")
    ap.add_argument("--preset", help="Preset name from queries.yaml (or 'all')")
    ap.add_argument("--max", type=int, default=30, help="max search results per query")
    ap.add_argument("--top", type=int, default=5, help="top N to clone+brief per query")
    ap.add_argument("--dry-run", action="store_true", help="score only, no cloning")
    args = ap.parse_args()

    queries = []
    if args.preset:
        presets = yaml.safe_load((BASE / "queries.yaml").read_text())
        if args.preset == "all":
            queries = [(k, v) for k, v in presets.items()]
        elif args.preset in presets:
            queries = [(args.preset, presets[args.preset])]
        else:
            sys.exit(f"Unknown preset. Available: {', '.join(presets)}")
    elif args.query:
        queries = [("custom", args.query)]
    else:
        sys.exit("Give --query or --preset")

    all_picks = []
    for tag, q in queries:
        picks = run_query(q, max_items=args.max, top=args.top,
                          dry_run=args.dry_run, tag=tag)
        all_picks.extend(picks)
        time.sleep(2)

    if all_picks:
        write_report(all_picks, args.preset or "custom")
    print(f"\nDone. {len(all_picks)} repos picked.")


if __name__ == "__main__":
    main()
