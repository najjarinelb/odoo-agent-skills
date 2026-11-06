---
name: mna-module
description: >-
  Scaffold an Odoo module that matches the target version, with no leftover
  attrs, tree or name_get. Use for "create a module", "new addon", "scaffold
  this", "I need a model for X", or any request to start custom Odoo
  development.
---

# mna-module

A module scaffolded for the wrong version installs cleanly and then breaks in a view nobody opens
until a client does. The version is the first question, not a detail.

```bash
python3 scaffold.py --name stock_alert --version 18.0 --prefix mna_ --model stock.alert
python3 scaffold.py --name stock_alert --version 16.0 --prefix mna_ --dry-run
```

## Before you write

1. Read `~/.claude/odoo/context.md` for the version, the module prefix, the author line and the
   licence. If it does not exist, **ask for the target version first.** Do not pick a default.
2. Ask what the module is for in one sentence. A module that cannot be described in one sentence is
   two modules.
3. Ask whether this extends an existing model or adds a new one. Extending is almost always the
   right answer and produces a quarter of the code.

## What the version changes

`scaffold.py` writes the correct form for the target. The differences that actually bite:

| | 16.0 | 17.0 | 18.0 and later |
|---|---|---|---|
| View conditions | `attrs="{'invisible': [...]}"` | plain `invisible="expr"` | plain `invisible="expr"` |
| List view tag | `<tree>` | `<tree>` | `<list>` |
| Action view mode | `tree,form` | `tree,form` | `list,form` |
| Display name | `name_get()` | `_compute_display_name` | `_compute_display_name` |

`attrs` and `states` were removed in 17.0. `<tree>` became `<list>` in 18.0. Writing the old form
for a new version is the single most common mistake when porting, and it is silent until render.

## Rules for the code itself

- Extend through inheritance. Never edit a core module.
- `self.env.company`, not `self.env.user.company_id`.
- `t-out` in QWeb, never `t-esc` or `t-raw`.
- Odoo exceptions only: `ValidationError`, `UserError`. Never a bare `Exception`.
- `_logger`, never `print`.
- Security first, not last. A module without `ir.model.access.csv` fails for every user who is not
  an administrator, and that is discovered in UAT by a client.
- No inline comments. If a line needs explaining, the name is wrong.

## After scaffolding

Install it and read the log before writing any logic:

```bash
odoo-bin -d <db> -i <prefix><name> --stop-after-init
```

An install that prints a warning is not an install that worked. Read it.

## The gate

This writes files on disk and nothing else. It does not install, it does not touch a database, and
it does not commit. Every run ends with the install command and the question: **did the log come
back clean?**
