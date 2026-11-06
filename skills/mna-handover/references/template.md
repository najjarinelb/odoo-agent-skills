# Handover: `<module_name>`

| | |
|---|---|
| Module | `<prefix_name>` |
| Odoo version | `<16.0 / 17.0 / 18.0 / 19.0>` |
| Deployment | `<on-premise docker / odoo.sh>` |
| Delivered | `<date>` |
| Author | `<name>` |
| Depends on | `<modules>` |

## 1. What it does

Two sentences. In the client's words, not in field names.

## 2. What will surprise you

The section that matters. One bullet per surprise, each with the reason.

- `<the decision>` because `<the constraint that forced it>`
- `<the thing that looks wrong but is not>` because `<why>`

If this section is empty, it has not been thought about properly. There is always at least one.

## 3. Files changed

| File | Why |
|---|---|
| `models/x.py` | |
| `views/x_views.xml` | |
| `security/ir.model.access.csv` | |

## 4. Configuration it depends on

What must be true in the database for this to work. Each line is a thing that, if changed, breaks
the module.

- `<setting or record>`: must be `<value>`, because `<reason>`

## 5. What it does not do

Scope discussed and excluded, with who decided.

- `<excluded thing>`, excluded on `<date>` by `<who>`, because `<why>`

## 6. How to verify it still works

Steps anyone can run without asking. Each step states its expected result.

1. `<action>` → expect `<result>`
2. `<action>` → expect `<result>`

## 7. Known limitations

| Limitation | Triggered when | Disclosed to client |
|---|---|---|
| | | yes / no |

## 8. Testing actually performed

Not testing planned. Testing performed, with what was not covered.

- Covered: `<cases>`
- Not covered: `<cases>`, because `<reason>`
