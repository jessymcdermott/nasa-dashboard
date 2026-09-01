# Use Case 3 — Supply Chain Risk & SBOM Blast-Radius Auditing (Demo Runbook)

**Target persona:** AppSec Managers / Security Analysts
**Harness:** Claude Code / Claude Desktop with the Black Duck SCA MCP server
**Instance:** https://sca377.poc.blackduck.com
**Project group:** `Black Duck Project Groups`

---

## Pre-seeded portfolio

| Project | Version | Components | Vulns (C/H/M/L) | project_id / version_id |
|---|---|---|---|---|
| `nasa-dashboard` | 1.2.3 | 19 | 2 / 43 / 39 / 34 | `c1c0ed75-f090-4242-be9e-691541ff7a87` / `a3b5d62b-b221-434e-8d7f-b048698ed57f` |
| `nasa-dashboard` | 2.0.0 | 19 | 2 / 43 / 39 / 34 | `c1c0ed75-f090-4242-be9e-691541ff7a87` / `2803eb00-88a4-42de-9678-ba4d927ed138` |
| `mission-telemetry-utils` | 2.1.4 | 5 | 2 / 20 / 14 / 12 | `72307bd9-9050-43f5-8227-87f85867c231` / `ae1fc141-5e7a-4358-8800-2bc9f95d45ce` |

- `nasa-dashboard` versions come from scanning the repo `requirements.txt` (flat list of 19 direct deps: Flask, Werkzeug, Jinja2, Pillow, lxml, cryptography, gunicorn, PyYAML, urllib3, certifi, requests, setuptools, wheel, python-dotenv, pyswisseph, axios, lodash, minimist, node-fetch).
- `mission-telemetry-utils` comes from scanning `package/` with a generated `package-lock.json`, so the BOM resolves **`follow-redirects@1.16.0` as a transitive dependency of `axios`**.

### Scan command notes
Detect needs `-detect.accuracy.required=NONE` for the `requirements.txt` parse (no lockfile / venv), plus `-detect.detector.search.depth=10`. Via the MCP `scan` tool:
`detect_extra_args = {"detect.accuracy.required": "NONE", "detect.detector.search.depth": "10"}`

---

## Blast-radius CVE

**`CVE-2026-40175`** (BDSA-2026-6870) — prototype-pollution "gadget" chain → RCE in `axios@0.21.0`, CVSS **9.3**.
Confirmed present in **all three** project versions.

Backup: **`CVE-2022-0235`** (BDSA-2022-0244) — cookie-header leak in `node-fetch@2.6.0`, CVSS 9.0, also spans all three.

---

## Optional: differentiate remediation status before recording

So prompt 2 shows a spread instead of everything reading "New". Run in an **interactive** Claude Code session (needs a permission prompt) or set in the Black Duck UI:

| Project version | Set status | Justification |
|---|---|---|
| `nasa-dashboard` 1.2.3 | `REMEDIATION_REQUIRED` | Legacy release line; upgrade axios per upgrade guidance |
| `nasa-dashboard` 2.0.0 | `UNDER_INVESTIGATION` | Current release; assessing exploitability |
| `mission-telemetry-utils` 2.1.4 | `NOT_AFFECTED` | Vulnerable code path not reachable |

Component IDs for the update: axios `component_id=0ddca5c6-f5a1-4417-86b1-14c3b79aca8a`,
`component_version_id=b6415082-538e-4c92-965c-0c9d3247fd75`; `vulnerability=BDSA-2026-6870`,
`related_vulnerability=CVE-2026-40175`.

---

## Demo script

### Prompt 1 — BOM inspection
> "Inspect the BOM for 'mission-telemetry-utils:2.1.4' and list all direct and transitive dependencies."

Assistant flow: resolve project by name -> list version -> pull BOM.
Expected 5 components: **axios 0.21.0** (direct, 1 crit / 12 high), **follow-redirects 1.16.0** (transitive, via axios), **lodash 4.17.15** (6 high), **minimist 1.2.0** (2 high), **node-fetch 2.6.0** (1 crit).

Swap in `nasa-dashboard:1.2.3` for the larger 19-component list (flatter, no tree).

### Prompt 2 — CVE blast radius
> "Find all project versions affected by CVE-2026-40175 and report their current remediation status."

Expected 3 hits: `mission-telemetry-utils 2.1.4`, `nasa-dashboard 2.0.0`, `nasa-dashboard 1.2.3`, each with its remediation status (New unless the optional step above was done).

### Prompt 3 (optional) — SBOM export
> "Generate an SBOM for nasa-dashboard:1.2.3."

Only one template is configured on this instance: **NTIA Minimum (SPDX 2.3, JSON)**.
Produces `sbomb/SBOM_nasa-dashboard_1.2.3_SPDX23.spdx.json` — 20 components, 20 relationships.
(Pre-generated; re-run live on camera if you want to show the flow.)

---

## Voiceover narration

**Setup (first prompt being typed):**
"Our AppSec team just inherited three services. Instead of opening the Black Duck console, an analyst asks Claude directly, in plain language, to inspect the bill of materials for one of them."

**Over prompt 1's result:**
"In one turn, Claude resolved the project, pulled its full BOM, and broke it down by direct versus transitive dependencies. Notice `follow-redirects` — nobody added that to `package.json`. It's in the build because `axios` depends on it, and Claude surfaces it alongside its risk. That's the supply-chain visibility problem, answered conversationally."

**Over prompt 2 being typed:**
"Now the harder question. A new critical drops — CVE-2026-40175, a remote-code-execution flaw in `axios`. The analyst needs to know: how far does this reach across our portfolio?"

**Over prompt 2's result:**
"Claude cross-references every project version in the instance and comes back with the blast radius — one vulnerable package, three shipping products — and for each one, its current remediation sub-status. The legacy 1.2.3 line needs an upgrade; 2.0.0 is under investigation; the telemetry utility was already assessed as not affected. That's a portfolio-wide triage picture in seconds, without touching the UI."

**Close:**
"SBOM auditing, vulnerability cross-referencing, and remediation tracking — driven from the same desktop AI harness the team already works in."
