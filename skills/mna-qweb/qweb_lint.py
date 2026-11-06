#!/usr/bin/env python3
"""Lint an Odoo QWeb report template for problems that show up in the PDF.

    python3 qweb_lint.py report_template.xml
    python3 qweb_lint.py /path/to/module/report/

Reads files. Changes nothing. Renders nothing: a clean lint is not a correct
PDF, it only means the known traps are absent.
"""

import argparse
import os
import re
import sys
import xml.etree.ElementTree as ET

MONETARY_HINT = re.compile(
    r"(amount|total|price|subtotal|balance|debit|credit|cost)", re.I)

CHECKS = [
    ("t-esc", "error",
     re.compile(r"\bt-esc\s*="),
     "t-esc is superseded by t-out."),

    ("t-raw", "error",
     re.compile(r"\bt-raw\s*="),
     "t-raw was removed. Use t-out."),

    ("t-field-options", "error",
     re.compile(r"\bt-field-options\s*="),
     "t-field-options became t-options."),

    ("hardcoded-company", "error",
     re.compile(r"(?i)>\s*(tel|phone|fax)[:\s]|@[\w.-]+\.(com|net|org|lb|ae|sa)\b"),
     "a phone number or email address in the template. Read it from "
     "company_id so the report survives a second company."),

    ("absolute-position", "warn",
     re.compile(r"position\s*:\s*absolute|position\s*:\s*fixed"),
     "absolute positioning does not survive the PDF engine reliably. Use "
     "tables or flow layout."),

    ("pixel-width", "warn",
     re.compile(r"width\s*:\s*\d{3,}px"),
     "a fixed pixel width over 99px is the usual cause of content cut off "
     "at the page edge. Use a percentage."),

    ("inline-font-size", "warn",
     re.compile(r"font-size\s*:\s*\d+px"),
     "pixel font sizes render differently in the PDF engine. Use pt."),

    ("img-base64", "warn",
     re.compile(r'src\s*=\s*["\']data:image'),
     "an inlined base64 image. Point at the company logo field instead."),

    ("direction-inline", "warn",
     re.compile(r'\bdir\s*=\s*["\']rtl["\']'),
     "direction set on an element. Set it once on the document body so the "
     "whole layout mirrors rather than just the text."),
]


def lint_text(path, text):
    out = []
    lines = text.splitlines()
    for cid, level, rx, msg in CHECKS:
        for no, line in enumerate(lines, 1):
            if rx.search(line):
                out.append((level, cid, path, no, line.strip()[:110], msg))

    for no, line in enumerate(lines, 1):
        m = re.search(r't-out\s*=\s*["\']([^"\']+)["\']', line)
        if m and MONETARY_HINT.search(m.group(1)) and "t-options" not in line:
            out.append((
                "error", "monetary-no-options", path, no, line.strip()[:110],
                "a monetary looking field printed without t-options. It will "
                "render with no currency symbol and default rounding."))
    return out


def lint_structure(path, text):
    out = []
    try:
        root = ET.fromstring(text)
    except ET.ParseError as exc:
        return [("error", "xml-parse", path, 0, str(exc),
                 "the file is not valid XML. Nothing else was checked.")]

    for rec in root.iter("record"):
        if rec.get("model") == "ir.actions.report":
            fields = {f.get("name") for f in rec.findall("field")}
            if "paperformat_id" not in fields:
                out.append((
                    "warn", "no-paperformat", path, 0, rec.get("id") or "",
                    "the report action sets no paperformat_id, so margins "
                    "fall back to a default."))

    has_template = any(el.tag == "template" for el in root.iter())
    if has_template and "web.external_layout" not in text:
        out.append((
            "warn", "no-external-layout", path, 0, "",
            "no call to web.external_layout. A hand built header loses the "
            "company block and the layout the client chose."))
    return out


def walk(target):
    if os.path.isfile(target):
        return [target]
    found = []
    for base, dirs, names in os.walk(target):
        dirs[:] = [d for d in dirs if d not in {".git", "__pycache__"}]
        found += [os.path.join(base, n) for n in names if n.endswith(".xml")]
    return sorted(found)


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("path", help="xml file or directory")
    p.add_argument("--errors-only", action="store_true")
    args = p.parse_args(argv)

    files = walk(args.path)
    if not files:
        print("no xml files found at %s" % args.path)
        return 2

    findings = []
    for path in files:
        try:
            with open(path, encoding="utf-8", errors="replace") as fh:
                text = fh.read()
        except OSError:
            continue
        findings += lint_text(path, text)
        findings += lint_structure(path, text)

    if args.errors_only:
        findings = [f for f in findings if f[0] == "error"]

    errors = [f for f in findings if f[0] == "error"]
    warns = [f for f in findings if f[0] == "warn"]

    print("linted %d file%s: %d error%s, %d warning%s"
          % (len(files), "" if len(files) == 1 else "s",
             len(errors), "" if len(errors) == 1 else "s",
             len(warns), "" if len(warns) == 1 else "s"))
    print()

    for label, group in (("ERRORS", errors), ("WARNINGS", warns)):
        if not group:
            continue
        print("== %s ==" % label)
        by_check = {}
        for f in group:
            by_check.setdefault(f[1], []).append(f)
        for cid in sorted(by_check, key=lambda c: -len(by_check[c])):
            hits = by_check[cid]
            print("\n%s  (%d)" % (cid, len(hits)))
            print("  %s" % hits[0][5])
            for f in hits[:6]:
                loc = "%s:%d" % (f[2], f[3]) if f[3] else f[2]
                print("    %s  %s" % (loc, f[4]))
            if len(hits) > 6:
                print("    ... and %d more" % (len(hits) - 6))
        print()

    print("a clean lint is not a correct PDF. render it and look at it.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
