# RepoBiz Finder

Find the best working open-source repositories, understand their licenses,
clone the permissive ones, and generate business productization briefs —
so an open-source repo becomes a sellable software product business.

## Pipeline

1. **Search** — GitHub search API (authenticated, via stored `custom.github`
   credential) with quality-biased queries.
2. **License check** — every repo's SPDX license is classified:
   - `SAFE` — MIT, Apache-2.0, BSD, ISC, Unlicense, CC0, Zlib… → can be
     cloned and turned into a closed commercial product (attribution kept).
   - `CAUTION` — MPL-2.0, LGPL, EPL… → usable with conditions, flagged for review.
   - `BLOCKED` — GPL/AGPL/SSPL/Elastic/BSL, custom, or **no license**
     (no license = all rights reserved) → never used for closed products.
3. **Quality score (0–100)** — stars/forks (log scale), push recency,
   open-issue health, completeness (description, homepage, topics).
   Archived/disabled repos score 0 and are dropped.
4. **Jev business scoring** — TypeSafe Jev (System One) rates each candidate:
   `productizable` probability + best monetization model
   (hosted SaaS / white-label / managed service / one-time product / plugin).
5. **Clone** — shallow `git clone --depth 1` of the top picks into `clones/`.
6. **Business brief** — `BUSINESS_BRIEF.md` per repo: what it is, license
   obligations, Jev verdict, productization plan, monetization model,
   README excerpt. Master table in `reports/report-<tag>-<ts>.md`.

## Usage

```bash
# Custom search (dry run = score only, no clone)
python3 run.py --query "self-hosted analytics stars:>300 pushed:>2025-01-01" --max 20 --top 3 --dry-run

# Preset category, clone top 5 + briefs
python3 run.py --preset self-hosted --top 5

# All presets
python3 run.py --preset all --top 3

# Daily hunt: all presets, Jev cash-ranked top 10, clone + brief, dedupe via state/seen.json
python3 run.py --daily10
```

Daily-10 ranking: `cash_score = 0.5 * productizable_p + 0.5 * fast_cash_p`,
where `fast_cash_p` is Jev's probability of first revenue within 60 days
for a solo dev with zero budget. Repos >150MB are skipped (disk sanity);
clones older than 14 days are pruned (briefs and reports are kept).

Presets live in `queries.yaml`: `dev-tools`, `ai-tools`, `self-hosted`,
`business-apps`, `productivity`, `marketing`, `dashboard`, `automation`.

## License discipline

- Every brief records the exact license + what you must do
  (e.g. MIT → keep copyright notice; Apache-2.0 → keep license text, note changes).
- Add a `THIRD_PARTY_LICENSES.md` to any product before distribution.
- `CAUTION` (weak copyleft) repos are flagged — get the conditions right
  before building a business on them.
- `BLOCKED` repos are never cloned by this tool.

## Layout

```
run.py                  # CLI orchestrator
queries.yaml            # search presets
repobiz/
  github_api.py         # GitHub REST via stored credential (never raw keys)
  license.py            # SPDX -> SAFE / CAUTION / BLOCKED
  quality.py            # 0-100 working-repo score
  jevbiz.py             # Jev productizable probability + monetization model
  productize.py         # shallow clone + BUSINESS_BRIEF.md
clones/                 # cloned repos (each with BUSINESS_BRIEF.md)
reports/                # ranked report per run
```
