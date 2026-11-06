---
name: mna-valuation
description: >-
  Reconcile Odoo stock valuation against the general ledger and explain a
  COGS figure nobody can account for. Use for "stock account doesn't match",
  "COGS is wrong", "inventory valuation report", "backdated stock entries",
  "negative remaining quantity", or any inventory and accounting mismatch.
---

# mna-valuation

The stock account and the valuation report disagree, and somebody has to say by how much and why.
This is that work, done in the right order.

```bash
ls queries/
psql -U odoo -d <db> -f queries/01_gl_vs_layers.sql
```

## Before any query

1. Read `~/.claude/odoo/context.md` for the version and the deployment.
2. Get three things from the client and do not start without them: **the date**, **the company**,
   and **the figure they believe is correct**. A reconciliation without a target is a tour of the
   data.
3. Confirm the costing method and the valuation setting per product category. Standard, FIFO and
   average cost fail in different ways and the queries mean different things for each.
4. Confirm whether valuation is automated or manual. On manual valuation the stock account is not
   supposed to follow the layers, and half of these queries do not apply.

## Order of work

The order matters, because each step narrows what the next one has to explain.

1. **`01_gl_vs_layers.sql`** gives the single number: the gap between the stock accounts and the
   valuation layers, per account, as of a date. Everything after this explains that number.
2. **`02_layers_without_entries.sql`** finds value that moved without a ledger entry. These are
   usually the whole gap.
3. **`03_negative_remaining.sql`** finds layers consumed below zero. This is what a backdated
   receipt does, and it is the usual cause of a COGS figure that cannot be traced.
4. **`04_layers_vs_quants.sql`** compares valued quantity against on-hand quantity. A gap here is a
   data problem, not an accounting one, and fixing the accounts first would be wrong.
5. **`05_cogs_by_period.sql`** attributes COGS to periods so the client can see which month moved.

## What backdating does, and why it matters

Validating a receipt with a date earlier than deliveries already posted against the same product
does not reorder the valuation layers. The outgoing moves were valued at the cost that existed when
they were validated. The layers stay in validation order, so remaining quantity goes negative and
the cost of the backdated receipt is never applied to the deliveries that preceded it.

Which means: **the stock account is not wrong, the sequence is.** Say this plainly to the client
before anyone proposes a journal entry, because an adjusting entry on top of a sequence problem
hides it rather than fixing it and the next month is worse.

## Before proposing any correction

- Say what the gap is, as one number, with the date it applies to.
- Say which of the five queries explains it and how much of it.
- Say whether the cause is code, data, or process. A client validating receipts a week late is a
  process cause and no module fixes it.
- Only then propose the correction, and name what it does not fix.

An adjusting entry is a last resort, not a first move. It needs the client's accountant to agree in
writing, and the reason recorded somewhere a future consultant will find it.

## The gate

Every query here is read only. Nothing in this skill writes to a database. A correction is a
decision the client makes with the numbers in front of them, and it is applied by hand after they
have agreed to it.
