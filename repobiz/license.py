"""License classification for business use.

Verdicts:
  SAFE     - permissive; can be cloned and turned into a closed commercial product
             (attribution / license-copy obligations still apply).
  CAUTION  - weak copyleft; usable but with conditions (share modifications of the
             covered files, etc.). Needs human review before productizing.
  BLOCKED  - strong copyleft, proprietary-ish, or no/unknown license. Do NOT build
             a closed business on these. (No license = all rights reserved.)
"""

# SPDX keys as returned by the GitHub API `license.key` field.
SAFE = {
    "mit": "Include the original copyright notice + MIT text in the product.",
    "apache-2.0": "Include the Apache-2.0 license text; state changes made to the code.",
    "bsd-2-clause": "Include the original copyright notice + BSD text.",
    "bsd-3-clause": "Include the original copyright notice + BSD text.",
    "bsd-3-clause-clear": "Include the original copyright notice + BSD text.",
    "isc": "Include the original copyright notice + ISC text.",
    "unlicense": "Public domain; no obligations (keep a note of origin anyway).",
    "cc0-1.0": "Public domain; no obligations (keep a note of origin anyway).",
    "zlib": "Include the copyright notice; do not misrepresent origin.",
    "artistic-2.0": "Include the license text; modified versions must be clearly marked.",
    "ms-pl": "Include the license text with distributions.",
}

CAUTION = {
    "mpl-2.0": "Weak copyleft: modifications to MPL-covered files must be shared under MPL-2.0. New separate files can stay proprietary.",
    "lgpl-2.1": "Weak copyleft: if linked as a library and kept replaceable, the app can stay proprietary; modified library itself must be shared.",
    "lgpl-3.0": "Weak copyleft: same as LGPL-2.1 plus anti-tivoization care on devices.",
    "epl-1.0": "Weak copyleft: modifications to EPL-covered modules must be shared under EPL.",
    "epl-2.0": "Weak copyleft: same as EPL-1.0, GPL-compatible secondary option exists.",
    "cddl-1.0": "Weak copyleft: modifications to CDDL-covered files must be shared.",
}

BLOCKED = {
    "gpl-2.0": "Strong copyleft: derivative product must be open-sourced under GPL-2.0. Not usable for a closed commercial product.",
    "gpl-3.0": "Strong copyleft: derivative product must be open-sourced under GPL-3.0. Not usable for a closed commercial product.",
    "agpl-3.0": "Strong copyleft + network clause: even SaaS use forces source disclosure. Not usable for a closed commercial product.",
    "sspl-1.0": "Source-available, NOT open source: offering it as a service forces publishing all management code. Blocked.",
    "elastic-2.0": "Source-available with field-of-use limits on managed services. Blocked.",
    "bsl-1.1": "Business Source License: time-delayed open source; commercial use restricted until the change date. Blocked.",
    "other": "Non-standard/custom license text — needs manual legal review. Blocked by default.",
    "noassertion": "GitHub could not determine a license — treat as unlicensed. Blocked.",
}


def classify(spdx_key, license_name=""):
    """Return (verdict, obligation_or_reason)."""
    key = (spdx_key or "").strip().lower()
    if not key:
        return ("BLOCKED", "No license declared = all rights reserved. Cannot use commercially.")
    if key in SAFE:
        return ("SAFE", SAFE[key])
    if key in CAUTION:
        return ("CAUTION", CAUTION[key])
    if key in BLOCKED:
        return ("BLOCKED", BLOCKED[key])
    return ("BLOCKED", f"Unknown license '{license_name or key}' — needs manual review. Blocked by default.")
