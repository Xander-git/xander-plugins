"""Helpers for the summarize-session skill.

Standalone, dependency-free logic. Run as a script from Claude Code:
    python3 kernel.py catalog          # print the three-tier section catalog
    python3 kernel.py scan FILE.md     # consistency-scan a composed summary
or import the helpers directly:
    from kernel import section_catalog, consistency_scan
"""

SECTION_CATALOG = {
    "spine": [
        {"key": "header", "title": "Header",
         "trigger": "always"},
        {"key": "original_request", "title": "Original request",
         "trigger": "always — verbatim first user message"},
        {"key": "decision_log", "title": "Decision & steering log",
         "trigger": "always — thin note if single-pass, framed by WHY"},
    ],
    "body": [
        {"key": "built", "title": "What was built / done",
         "trigger": "any work product or substantive action"},
        {"key": "sources", "title": "External sources & dependencies",
         "trigger": "any network fetch, API/MCP call, or package install"},
        {"key": "transformations", "title": "Data / code transformations",
         "trigger": "input ingested and reshaped/refactored from a source"},
        {"key": "caveats", "title": "Methodological caveats",
         "trigger": "a non-obvious method/parameter/design choice was made"},
        {"key": "validation", "title": "Validation / testing",
         "trigger": "tests, controls, linters, or sanity checks were run"},
        {"key": "corrections", "title": "Corrections / course changes",
         "trigger": "a prior output was revised or a claim retracted"},
        {"key": "next_steps", "title": "Planned / next steps",
         "trigger": "work remains unfinished or explicitly deferred"},
    ],
    "close": [
        {"key": "lessons", "title": "Lessons learned",
         "trigger": "always"},
        {"key": "artifact_index", "title": "Artifact index",
         "trigger": "always — states 'none' only if zero artifacts"},
    ],
}


def section_catalog():
    """Return the three-tier section catalog (spine / body / close).

    Body sections are evidence-gated and keep this relative order; the catalog
    is a FLOOR — mint extra body sections for substantial uncaptured threads.
    """
    return SECTION_CATALOG


def extract_tokens(text):
    """Return [(norm_token, kind, line_no, snippet)] for numbers and IDs.

    Numbers are normalized by stripping thousands-separators and a trailing '%'
    so '2,640' and '2640' compare equal. IDs cover common software identifiers:
    git SHAs, issue/PR refs (#123), and version tags (v1.2.3).
    """
    import re
    num_re = re.compile(r"\d[\d,]*(?:\.\d+)?%?")
    id_re = re.compile(r"\b[0-9a-f]{7,40}\b|#\d+|\bv\d+(?:\.\d+)+\b")
    out = []
    for i, line in enumerate(text.splitlines(), 1):
        snip = line.strip()[:140]
        for m in num_re.finditer(line):
            norm = m.group().rstrip("%").replace(",", "")
            if norm and norm not in (".",):
                out.append((norm, "number", i, snip))
        for m in id_re.finditer(line):
            out.append((m.group(), "id", i, snip))
    return out


def consistency_scan(text, min_value=100.0, rel_tol=0.05):
    """Support the internal-consistency rule before saving a summary.

    Returns {"repeated": {token: [(line, snippet), ...]}, "near_miss": [...]}.
    - repeated: every number/ID appearing on more than one line, with locations,
      so repeats can be eyeballed for agreement.
    - near_miss: pairs of distinct numeric values that are close (relative diff
      below rel_tol), both at least min_value, and share a >=4-letter context
      word — the classic 'same quantity stated two ways' bug.
    """
    import re
    toks = extract_tokens(text)

    by_token = {}
    for norm, kind, ln, snip in toks:
        by_token.setdefault((kind, norm), []).append((ln, snip))
    repeated = {}
    for (kind, norm), occ in by_token.items():
        uniq = sorted(set(occ))
        if len({l for l, _ in uniq}) > 1:
            repeated[norm] = uniq

    words_re = re.compile(r"[A-Za-z]{4,}")
    info = {}
    for norm, kind, ln, snip in toks:
        if kind != "number":
            continue
        try:
            val = float(norm)
        except ValueError:
            continue
        rec = info.setdefault(norm, [val, set(), set()])
        rec[1].update(w.lower() for w in words_re.findall(snip))
        rec[2].add(ln)

    near_miss = []
    keys = list(info)
    for a in range(len(keys)):
        for b in range(a + 1, len(keys)):
            va, wa, la = info[keys[a]]
            vb, wb, lb = info[keys[b]]
            if va == vb:
                continue
            hi = max(abs(va), abs(vb))
            if hi < min_value:
                continue
            rel = abs(va - vb) / hi
            shared = wa & wb
            if 0 < rel < rel_tol and shared:
                near_miss.append({
                    "a": keys[a], "b": keys[b], "rel_diff": round(rel, 4),
                    "shared_context": sorted(shared)[:6],
                    "lines_a": sorted(la), "lines_b": sorted(lb),
                })
    return {"repeated": repeated, "near_miss": near_miss}


def _main(argv):
    """CLI: `catalog` prints the section catalog; `scan FILE` scans a summary."""
    import json
    import sys

    cmd = argv[1] if len(argv) > 1 else ""
    if cmd == "catalog":
        print(json.dumps(section_catalog(), indent=2))
        return 0
    if cmd == "scan" and len(argv) > 2:
        with open(argv[2], encoding="utf-8") as fh:
            scan = consistency_scan(fh.read())
        print(json.dumps(scan, indent=2))
        if scan["near_miss"]:
            print(
                f"\n{len(scan['near_miss'])} near-miss pair(s) — resolve before "
                "saving.", file=sys.stderr)
            return 1
        print("\nNo near-miss numeric pairs.", file=sys.stderr)
        return 0
    print("usage: python3 kernel.py catalog | scan <file.md>", file=sys.stderr)
    return 2


if __name__ == "__main__":
    import sys
    raise SystemExit(_main(sys.argv))
