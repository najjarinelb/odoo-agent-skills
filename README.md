# odoo-agent-skills

Six Claude skills for Odoo implementation work, built on one rule: **diagnose before you code.**

Most wrong Odoo code is written against a guess about data. The guess is usually reasonable, usually
wrong, and the cost lands on a client at month end. These skills are built so the agent reaches for
a read-only query before it reaches for a patch.

Nothing here writes to a database, installs a module, or commits anything. The tools emit commands,
scaffold files and report findings. You run them, you read the output, you decide.

## The skills

| Skill | Use it to |
|---|---|
| `/mna-diagnose` | Get the read-only psql that proves what is actually wrong, before writing a fix |
| `/mna-module` | Scaffold a module that matches the target version, with no leftover `attrs`, `tree` or `name_get` |
| `/mna-upgrade` | Scan custom modules for code the target version removed, tiered by how certain the finding is |
| `/mna-qweb` | Write and lint QWeb PDF reports, including right-to-left Arabic layouts |
| `/mna-valuation` | Reconcile stock valuation against the ledger and explain an untraceable COGS figure |
| `/mna-handover` | Write the handover document for the next consultant, not for the filing cabinet |

## Tools

Plain Python 3. No dependencies, no network calls, no database connections.

| Tool | Does |
|---|---|
| `dx.py` | 32 read-only diagnostics across 10 symptoms, each with what the output means |
| `scaffold.py` | Version-correct module skeleton for 16.0 through 19.0 |
| `check_compat.py` | Deprecation scanner, findings split into confirmed and verify |
| `qweb_lint.py` | QWeb report linter for the problems that only appear in the PDF |
| `queries/*.sql` | Five ordered stock valuation reconciliation queries |

```bash
python3 dx.py --list
python3 dx.py stock-valuation

python3 scaffold.py --name stock_alert --version 18.0 --dry-run

python3 check_compat.py /path/to/module --target 18.0
python3 check_compat.py /path/to/module --target 18.0 --only confirmed

python3 qweb_lint.py /path/to/module/report/
```

`dx.py` refuses to print any query containing a writing statement. A diagnostic cannot be pasted
into psql and quietly change client data.

## Install

**Claude Code**, all projects:

```bash
git clone https://github.com/najjarinelb/odoo-agent-skills
cp -r odoo-agent-skills/skills/mna-* ~/.claude/skills/
```

**One project only**: copy into `./.claude/skills/` instead.

**Claude plugin marketplace**: the repo carries `.claude-plugin/`, so it installs as one pack.

**claude.ai or Claude Desktop**: zip a single skill folder so the zip contains `mna-diagnose/SKILL.md`
at its root, then upload it under Settings, Capabilities, Skills. Note that the Python tools will
not run in every surface, and the skills still work without them, with less precision.

## Set up your context file first

Every skill reads `~/.claude/odoo/context.md` before doing anything. Copy the template and fill it
in:

```bash
mkdir -p ~/.claude/odoo
cp odoo-agent-skills/templates/context.md ~/.claude/odoo/context.md
```

It holds your versions and deployments, your module prefix, your author line, how you reach each
environment, and your delivery format. Ten minutes here is worth more than any prompt, because Odoo
work is version specific and environment specific.

**Keep that file out of any public repository.** It describes real systems. The `.gitignore` here
already excludes `context.md` while keeping the template.

## What these skills will not do

Stated plainly, because a tool that overstates itself is worse than no tool.

- **`check_compat.py` is a regex scanner.** It finds removed syntax. It does not find behaviour that
  still parses but now does something different, a field renamed where the old name is built by
  string concatenation, or anything in a `.js` or `.scss` asset, where the OWL changes between
  versions are the real work. The scan starts an estimate. It does not finish one.
- **Findings are tiered on purpose.** `confirmed` means the removal is certain and the replacement is
  known. `verify` means the pattern changed around that release but the exact version or replacement
  needs checking against a running instance. Do not present a `verify` finding to a client as fact.
- **Version rules are written against 16.0 through 18.0.** The 19.0 behaviour is treated as matching
  18.0 where no change is known, which is an assumption and not a verified claim. If you work on
  19.0, confirm against your own instance and send a pull request.
- **A clean QWeb lint is not a correct PDF.** It means the known traps are absent. Render it and look
  at it.
- **`dx.py` queries assume Odoo 16 or later**, where translated fields are `jsonb`. On 15 and
  earlier, replace `name->>'en_US'` with `name`. Most also assume `company_id = 1`; change it.
- **No query here has been run against every Odoo version.** Read a query before you run it. That is
  the habit the whole pack is arguing for, and it applies to the pack itself.

## The gate

Every skill ends the same way: with the command to run and a question about its output. None of them
end with a finished change. That is deliberate. The agent does the reading, the recall and the
drafting. The decision stays with the consultant who has to answer for it.

## Contributing

Pull requests welcome, particularly:

- 19.0 version rules confirmed against a real instance, which moves a rule from `verify` to
  `confirmed`
- Additional diagnostic symptoms, as long as every query is read only and carries a line on what its
  output means
- Localization patterns for other regions

## Licence

MIT. See `LICENSE`.

Built by [Mohammad Najjarine](https://github.com/najjarinelb), Odoo technical consultant, from
delivery work across Lebanon, the UAE, Saudi Arabia and the DRC.
