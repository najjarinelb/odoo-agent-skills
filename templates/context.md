# context.md

Copy this to `~/.claude/odoo/context.md` and fill it in. Every skill in this pack reads it before
doing anything.

Ten minutes here is worth more than any prompt, because Odoo work is version specific and
environment specific. A module scaffolded for the wrong version installs and then breaks in a view
you do not look at until a client does.

## Versions I work on

Which Odoo versions, and which deployment for each. Be exact, because the rules differ.

```
16.0  community   on-premise docker
17.0  enterprise  odoo.sh
18.0  enterprise  on-premise docker
19.0  enterprise  odoo.sh
```

## Module prefix

The prefix for modules I author. Underscores, Odoo convention.

```
mna_
```

Per client, override it. A module delivered to a client usually carries their prefix or the
consultancy's, not mine.

```
clientname_
```

## Author and licence

What goes in `__manifest__.py`.

```
author:  Mohammad Najjarine
licence: LGPL-3
website:
```

## How I reach each environment

The command that gets me a shell and a psql prompt. Fill in your own, never commit real hosts or
credentials to a repo.

```
shell:   docker exec -it <container> bash
psql:    docker exec -it <db-container> psql -U odoo -d <database>
logs:    docker logs -f --tail 200 <container>
odoo.sh: via the web shell, or `odoo-bin shell -d <db>` on the build
```

## What I will not do without checking first

The rule the skills enforce on my behalf. Mine reads:

```
Never write code against an assumption about data. Diagnose in psql or the server shell first,
read the output, then write the minimum change that fixes the actual cause.
```

## Delivery format

How changed work leaves me.

```
Deliver only changed files, not full module zips.
No inline code comments.
Minimal diffs. Practical fix over theoretical refactor.
```

## Client context

Optional. One line per active account: version, deployment, and the thing that makes it unusual.
This is what stops a skill suggesting a v18 pattern on a v16 database.

```
<client>  16.0  docker    backdated stock valuation, multi-company
<client>  17.0  on-prem   custom purchase approval chain
<client>  18.0  docker    POS, two warehouses
```

Keep this file out of any public repository. It describes real systems.
