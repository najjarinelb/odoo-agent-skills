#!/usr/bin/env python3
"""Scan an Odoo module for code the target version removed.

    python3 check_compat.py /path/to/module --target 18.0
    python3 check_compat.py /path/to/addons --target 19.0 --only confirmed

Findings are tiered. "confirmed" means the removal is certain and the
replacement is known. "verify" means the pattern changed around that release
but the exact version or replacement needs checking against a running
instance before anything is changed.

Reads files. Changes nothing.
"""

import argparse
import os
import re
import sys

SKIP_DIRS = {".git", "__pycache__", "node_modules", ".idea", ".vscode"}

# (id, removed_in, tier, extensions, regex, message)
RULES = [
    ("attrs", 17.0, "confirmed", (".xml",),
     r'\battrs\s*=\s*["\']',
     "attrs was removed in 17.0. Use invisible, readonly or required with a "
     "plain python expression."),

    ("states-attr", 17.0, "confirmed", (".xml",),
     r'<(?:field|button|page|group)[^>]*\bstates\s*=\s*["\']',
     "the states view attribute was removed in 17.0. Use invisible with an "
     "expression on state."),

    ("tree-tag", 18.0, "confirmed", (".xml",),
     r"</?tree(?:\s|>|/>)",
     "the tree tag became list in 18.0."),

    ("view-mode-tree", 18.0, "confirmed", (".xml",),
     r'<field\s+name="view_mode">[^<]*\btree\b',
     "view_mode tree became list in 18.0."),

    ("name-get", 17.0, "confirmed", (".py",),
     r"\bdef\s+name_get\s*\(",
     "name_get was removed in 17.0. Compute display_name through "
     "_compute_display_name."),

    ("t-esc", 15.0, "confirmed", (".xml",),
     r"\bt-esc\s*=",
     "t-esc is superseded by t-out."),

    ("t-raw", 15.0, "confirmed", (".xml",),
     r"\bt-raw\s*=",
     "t-raw was removed. Use t-out."),

    ("t-field-options", 14.0, "confirmed", (".xml",),
     r"\bt-field-options\s*=",
     "t-field-options became t-options."),

    ("api-multi", 13.0, "confirmed", (".py",),
     r"@api\.multi\b",
     "api.multi was removed in 13.0. Recordset methods need no decorator."),

    ("api-one", 13.0, "confirmed", (".py",),
     r"@api\.one\b",
     "api.one was removed in 13.0. Iterate over self instead."),

    ("user-company", 13.0, "confirmed", (".py",),
     r"\.user\.company_id\b",
     "use self.env.company rather than self.env.user.company_id."),

    ("track-visibility", 12.0, "confirmed", (".py",),
     r"\btrack_visibility\s*=",
     "track_visibility became tracking."),

    ("account-invoice", 13.0, "confirmed", (".py", ".xml"),
     r"\baccount\.invoice\b",
     "account.invoice was merged into account.move in 13.0."),

    ("oldname", 13.0, "confirmed", (".py",),
     r"\boldname\s*=",
     "the oldname field argument was removed in 13.0. Rename in a migration "
     "script instead."),

    ("dp-precision", 12.0, "confirmed", (".py",),
     r"\bdp\.get_precision\s*\(|digits_compute\s*=",
     "pass digits as a named precision string instead."),

    ("old-api", 10.0, "confirmed", (".py",),
     r"\bosv\.osv\b|\b_columns\s*=|\bfields\.function\s*\(",
     "pre-9.0 API. This needs rewriting, not patching."),

    ("qty-done", 17.0, "verify", (".py", ".xml"),
     r"\bqty_done\b",
     "stock.move.line quantity fields were reworked around 17.0. Confirm the "
     "current field name on the target version before changing this."),

    ("user-has-groups", 17.0, "verify", (".py",),
     r"\buser_has_groups\s*\(",
     "user_has_groups was deprecated in favour of a has_group call. Confirm "
     "the exact signature on the target version."),

    ("oe-chatter", 18.0, "verify", (".xml",),
     r'class\s*=\s*["\'][^"\']*oe_chatter',
     "the chatter markup changed around 18.0 in favour of a chatter tag. "
     "Confirm against the target version before editing."),

    ("settings-div", 17.0, "verify", (".xml",),
     r'class\s*=\s*["\'][^"\']*o_setting_box',
     "res.config.settings markup changed around 17.0. Confirm the current "
     "structure before porting a settings page."),
]


def applicable(rule, target):
    return rule[1] <= float(target)


def walk(root):
    if os.path.isfile(root):
        yield root
        return
    for base, dirs, names in os.walk(root):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for n in names:
            if n.endswith((".py", ".xml")):
                yield os.path.join(base, n)


def scan(root, target, only=None):
    findings = []
    rules = [r for r in RULES if applicable(r, target)]
    if only:
        rules = [r for r in rules if r[2] == only]
    compiled = [(r[0], r[2], r[3], re.compile(r[4]), r[5], r[1]) for r in rules]

    for path in walk(root):
        ext = os.path.splitext(path)[1]
        try:
            with open(path, encoding="utf-8", errors="replace") as fh:
                lines = fh.read().splitlines()
        except OSError:
            continue
        for rid, tier, exts, rx, msg, removed in compiled:
            if ext not in exts:
                continue
            for no, line in enumerate(lines, 1):
                if rx.search(line):
                    findings.append({
                        "rule": rid, "tier": tier, "removed": removed,
                        "path": path, "line": no,
                        "text": line.strip()[:120], "message": msg,
                    })
    return findings


def report(findings, root, target):
    confirmed = [f for f in findings if f["tier"] == "confirmed"]
    verify = [f for f in findings if f["tier"] == "verify"]

    print("scanned %s against Odoo %s" % (root, target))
    print("%d confirmed, %d to verify" % (len(confirmed), len(verify)))
    print()

    for label, group in (("CONFIRMED", confirmed), ("VERIFY", verify)):
        if not group:
            continue
        print("== %s ==" % label)
        by_rule = {}
        for f in group:
            by_rule.setdefault(f["rule"], []).append(f)
        for rid in sorted(by_rule, key=lambda r: -len(by_rule[r])):
            hits = by_rule[rid]
            print("\n%s  (%d hit%s, removed in %s)"
                  % (rid, len(hits), "" if len(hits) == 1 else "s",
                     hits[0]["removed"]))
            print("  %s" % hits[0]["message"])
            for f in hits[:8]:
                print("    %s:%d  %s" % (f["path"], f["line"], f["text"]))
            if len(hits) > 8:
                print("    ... and %d more" % (len(hits) - 8))
        print()

    if not findings:
        print("no matches. that is not the same as upgrade-ready:")
        print("install on a restored copy at the target version and read the log.")
    else:
        print("next: fix confirmed, verify the rest against the target version,")
        print("then install on a restored copy of the real database and read the log.")


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("path", help="module or addons directory")
    p.add_argument("--target", required=True, help="target version, e.g. 18.0")
    p.add_argument("--only", choices=["confirmed", "verify"])
    p.add_argument("--rules", action="store_true", help="list rules and exit")
    args = p.parse_args(argv)

    if args.rules:
        for rid, removed, tier, exts, _rx, msg in RULES:
            print("%-18s %-6s %-9s %s" % (rid, removed, tier, ",".join(exts)))
        return 0

    if not os.path.exists(args.path):
        print("no such path: %s" % args.path)
        return 2

    report(scan(args.path, args.target, args.only), args.path, args.target)
    return 0


if __name__ == "__main__":
    sys.exit(main())
