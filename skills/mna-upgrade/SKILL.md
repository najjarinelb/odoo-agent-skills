---
name: mna-upgrade
description: >-
  Scan a custom Odoo module for code that the target version removed, before
  the upgrade rather than during it. Use for "upgrade this module", "migrate
  to v18", "port this to 19", "what breaks if we upgrade", or a version jump
  on any custom addon.
---

# mna-upgrade

An upgrade fails on the things nobody listed. This lists them first.

```bash
python3 check_compat.py /path/to/module --target 18.0
python3 check_compat.py /path/to/addons --target 19.0 --only confirmed
```

## Before you scan

1. Read `~/.claude/odoo/context.md` for the current version and the target.
2. Scan **every** custom module, not the one the ticket mentions. The module that breaks the upgrade
   is usually a small one somebody wrote two years ago and nobody lists as custom.
3. Record the current version of each module from its manifest. A module whose manifest version
   does not match the database is already in an unclear state and that is a separate problem.

## What the scanner reports, and how much to trust it

Findings come in two tiers, and the distinction matters more than the count.

- **confirmed**: the removal is certain and the replacement is known. Fix these.
- **verify**: the pattern changed around the target version but the exact release or the exact
  replacement needs checking against a running instance. **Confirm before changing anything.**
  Do not present a verify finding to a client as a fact.

This split is deliberate. A scanner that reports everything with equal confidence trains you to
ignore it.

## What it will not tell you

A regex scanner finds removed syntax. It does not find:

- Behaviour that still parses but now does something different.
- A field that was renamed but whose old name is built by string concatenation.
- Anything in a `.js` or `.scss` asset, where the OWL changes between versions are the real work.
- Data that the new version validates more strictly than the old one.

So the scan is the start of the estimate, never the whole of it. After the scan, install the module
on a copy at the target version and read the log. That is the only output that settles it.

## Order of work

1. Scan. Fix every confirmed finding.
2. Verify each verify finding against the target version source or a test instance.
3. Install on a restored copy of the real database, not an empty one. Empty databases pass upgrades
   that real data fails.
4. Read the log end to end.
5. Then, and only then, give an estimate.

## The gate

This reads files and reports. It changes nothing, installs nothing and touches no database. Every
run ends with: **how many confirmed, how many to verify, and the install command for a copy.**
