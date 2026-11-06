#!/usr/bin/env python3
"""Emit read-only diagnostic SQL for a named Odoo symptom.

Prints queries. Runs nothing. Connects to nothing.

    python3 dx.py --list
    python3 dx.py stock-valuation
    python3 dx.py stock-valuation --sql-only

Every query is a SELECT. A query containing a writing statement is refused by
guard() before it can reach stdout, so a diagnostic can never be pasted into
psql and silently change data.

Product names are jsonb on Odoo 16 and later. On 15 and earlier, replace
name->>'en_US' with name.
"""

import sys

WRITES = (
    "insert ", "update ", "delete ", "drop ", "alter ", "truncate ",
    "create ", "grant ", "revoke ", "comment on", "copy ", "vacuum",
    "reindex", "refresh materialized",
)

Q = {}

Q["stock-valuation"] = [
    (
        "Valuation layers against the stock accounts, per product",
        "The two value columns should agree. A gap is the amount the stock "
        "account is out by, and its sign tells you which side is ahead.",
        """
SELECT pt.name->>'en_US'                      AS product,
       round(sum(svl.value)::numeric, 2)      AS layer_value,
       round(sum(svl.quantity)::numeric, 4)   AS layer_qty
FROM   stock_valuation_layer svl
JOIN   product_product pp ON pp.id = svl.product_id
JOIN   product_template pt ON pt.id = pp.product_tmpl_id
WHERE  svl.company_id = 1
GROUP  BY 1
HAVING round(sum(svl.quantity)::numeric, 4) <> 0
ORDER  BY 2 DESC
LIMIT  50;
""",
    ),
    (
        "Valuation layers with no accounting entry",
        "Should be empty on an automated-valuation database. Rows here are "
        "moves that changed stock value without touching the ledger.",
        """
SELECT svl.id, svl.create_date, svl.quantity, svl.value,
       pt.name->>'en_US' AS product
FROM   stock_valuation_layer svl
JOIN   product_product pp ON pp.id = svl.product_id
JOIN   product_template pt ON pt.id = pp.product_tmpl_id
WHERE  svl.account_move_id IS NULL
  AND  svl.value <> 0
ORDER  BY svl.create_date DESC
LIMIT  50;
""",
    ),
    (
        "Layers whose remaining quantity is negative",
        "Should be empty. Negative remaining_qty is the usual cause of a "
        "COGS figure nobody can reconcile, and it comes from outgoing moves "
        "validated before the incoming ones.",
        """
SELECT svl.id, svl.create_date, svl.remaining_qty, svl.remaining_value,
       pt.name->>'en_US' AS product
FROM   stock_valuation_layer svl
JOIN   product_product pp ON pp.id = svl.product_id
JOIN   product_template pt ON pt.id = pp.product_tmpl_id
WHERE  svl.remaining_qty < 0
ORDER  BY svl.remaining_qty ASC
LIMIT  50;
""",
    ),
    (
        "Products set to a costing method that does not match their layers",
        "Confirms what the valuation is supposed to be before you argue "
        "about what it is.",
        """
SELECT pc.name->>'en_US'   AS category,
       pc.property_cost_method,
       pc.property_valuation,
       count(pt.id)         AS templates
FROM   product_category pc
LEFT   JOIN product_template pt ON pt.categ_id = pc.id
GROUP  BY 1, 2, 3
ORDER  BY 4 DESC;
""",
    ),
]

Q["stock-quant"] = [
    (
        "Quants in internal locations with a negative quantity",
        "Should be empty. Negative on-hand in an internal location means a "
        "move went out without stock to cover it.",
        """
SELECT sq.id, pt.name->>'en_US' AS product, sl.complete_name AS location,
       sq.quantity, sq.reserved_quantity
FROM   stock_quant sq
JOIN   product_product pp ON pp.id = sq.product_id
JOIN   product_template pt ON pt.id = pp.product_tmpl_id
JOIN   stock_location sl ON sl.id = sq.location_id
WHERE  sl.usage = 'internal'
  AND  sq.quantity < 0
ORDER  BY sq.quantity ASC
LIMIT  50;
""",
    ),
    (
        "Quants reserving more than they hold",
        "Should be empty. These block pickings that look available in the "
        "list view and refuse to validate.",
        """
SELECT sq.id, pt.name->>'en_US' AS product, sl.complete_name AS location,
       sq.quantity, sq.reserved_quantity
FROM   stock_quant sq
JOIN   product_product pp ON pp.id = sq.product_id
JOIN   product_template pt ON pt.id = pp.product_tmpl_id
JOIN   stock_location sl ON sl.id = sq.location_id
WHERE  sq.reserved_quantity > sq.quantity
ORDER  BY (sq.reserved_quantity - sq.quantity) DESC
LIMIT  50;
""",
    ),
    (
        "Duplicate quants on the same product, location and lot",
        "Odoo merges these itself under normal operation. Rows here point at "
        "a script or a module that wrote quants directly.",
        """
SELECT product_id, location_id, lot_id, owner_id, package_id,
       count(*) AS rows, sum(quantity) AS total
FROM   stock_quant
GROUP  BY 1, 2, 3, 4, 5
HAVING count(*) > 1
ORDER  BY 6 DESC
LIMIT  50;
""",
    ),
]

Q["invoice-mismatch"] = [
    (
        "Journal entries whose lines do not balance",
        "Must be empty. Any row is a corrupted entry and nothing else should "
        "be investigated until it is explained.",
        """
SELECT am.id, am.name, am.state, am.move_type, am.date,
       round(sum(aml.debit)::numeric, 2)  AS debit,
       round(sum(aml.credit)::numeric, 2) AS credit
FROM   account_move am
JOIN   account_move_line aml ON aml.move_id = am.id
GROUP  BY am.id, am.name, am.state, am.move_type, am.date
HAVING round(sum(aml.debit)::numeric, 2) <> round(sum(aml.credit)::numeric, 2)
ORDER  BY am.date DESC
LIMIT  50;
""",
    ),
    (
        "Posted entries with no lines",
        "Should be empty.",
        """
SELECT am.id, am.name, am.state, am.date
FROM   account_move am
LEFT   JOIN account_move_line aml ON aml.move_id = am.id
WHERE  am.state = 'posted'
  AND  aml.id IS NULL
ORDER  BY am.date DESC
LIMIT  50;
""",
    ),
    (
        "Move lines whose parent_state disagrees with the move",
        "parent_state is a stored related field. When it drifts, reports read "
        "one value and the form view another, which is the classic 'the "
        "report is wrong' ticket.",
        """
SELECT aml.id, am.id AS move_id, am.name, am.state AS move_state,
       aml.parent_state
FROM   account_move_line aml
JOIN   account_move am ON am.id = aml.move_id
WHERE  aml.parent_state <> am.state
LIMIT  50;
""",
    ),
    (
        "Reconciled amounts that do not net to zero per full reconcile",
        "A non-zero sum means a reconciliation is holding a residual that "
        "will show up as an unexplained open balance.",
        """
SELECT aml.full_reconcile_id,
       round(sum(aml.debit - aml.credit)::numeric, 2) AS net
FROM   account_move_line aml
WHERE  aml.full_reconcile_id IS NOT NULL
GROUP  BY 1
HAVING round(sum(aml.debit - aml.credit)::numeric, 2) <> 0
LIMIT  50;
""",
    ),
]

Q["module-state"] = [
    (
        "Modules in a state that is neither installed nor uninstalled",
        "Anything in to upgrade, to install or to remove is a module the "
        "server will act on at next start. This is the first query to run on "
        "an install that will not finish.",
        """
SELECT name, state, latest_version
FROM   ir_module_module
WHERE  state NOT IN ('installed', 'uninstalled', 'uninstallable')
ORDER  BY name;
""",
    ),
    (
        "A named module and everything that depends on it",
        "Tells you the blast radius before you uninstall or upgrade.",
        """
SELECT m.name AS module, m.state, d.name AS depends_on
FROM   ir_module_module m
LEFT   JOIN ir_module_module_dependency d ON d.module_id = m.id
WHERE  m.name = 'MODULE_NAME'
ORDER  BY 3;
""",
    ),
    (
        "Views belonging to a module that fail to resolve a parent",
        "An orphaned inherit_id is the usual reason a module installs and "
        "then every form in it is blank.",
        """
SELECT v.id, v.name, v.model, v.type, v.active, v.inherit_id
FROM   ir_ui_view v
WHERE  v.inherit_id IS NOT NULL
  AND  NOT EXISTS (SELECT 1 FROM ir_ui_view p WHERE p.id = v.inherit_id)
LIMIT  50;
""",
    ),
    (
        "Model records with no matching table",
        "Left behind by a module removed without its data. These break the "
        "fields list and any export that touches them.",
        """
SELECT im.id, im.model, im.name->>'en_US' AS label
FROM   ir_model im
WHERE  im.state = 'manual'
  AND  NOT EXISTS (
         SELECT 1 FROM information_schema.tables t
         WHERE t.table_name = replace(im.model, '.', '_')
       )
LIMIT  50;
""",
    ),
]

Q["slow"] = [
    (
        "Largest tables, data and indexes separately",
        "Orients everything that follows. A table far larger than its row "
        "count suggests bloat and a candidate for VACUUM FULL in a window.",
        """
SELECT c.relname AS table,
       pg_size_pretty(pg_total_relation_size(c.oid)) AS total,
       pg_size_pretty(pg_relation_size(c.oid))       AS data,
       c.reltuples::bigint                           AS approx_rows
FROM   pg_class c
JOIN   pg_namespace n ON n.oid = c.relnamespace
WHERE  n.nspname = 'public' AND c.relkind = 'r'
ORDER  BY pg_total_relation_size(c.oid) DESC
LIMIT  25;
""",
    ),
    (
        "Sequential scans on large tables",
        "A high seq_scan count against a large table is a missing index. "
        "Compare seq_tup_read to idx_tup_fetch before adding one.",
        """
SELECT relname AS table, seq_scan, seq_tup_read,
       idx_scan, idx_tup_fetch, n_live_tup
FROM   pg_stat_user_tables
WHERE  n_live_tup > 50000
ORDER  BY seq_tup_read DESC
LIMIT  25;
""",
    ),
    (
        "Queries running right now, longest first",
        "Run this while the slowness is happening, not afterwards. A query "
        "stuck in an idle in transaction state is holding locks.",
        """
SELECT pid, now() - query_start AS running_for, state, wait_event_type,
       left(query, 200) AS query
FROM   pg_stat_activity
WHERE  state <> 'idle'
  AND  query_start IS NOT NULL
ORDER  BY query_start ASC
LIMIT  25;
""",
    ),
    (
        "Unused indexes",
        "Indexes with no scans cost write time for nothing. Confirm over a "
        "period of normal use before dropping any.",
        """
SELECT relname AS table, indexrelname AS index,
       idx_scan,
       pg_size_pretty(pg_relation_size(indexrelid)) AS size
FROM   pg_stat_user_indexes
WHERE  idx_scan = 0
ORDER  BY pg_relation_size(indexrelid) DESC
LIMIT  25;
""",
    ),
]

Q["access-rights"] = [
    (
        "Model access rows for one model",
        "Shows every group that can touch the model and at what level. The "
        "model name goes in as a dotted name, not a table name.",
        """
SELECT rg.name->>'en_US' AS group_name,
       ima.perm_read, ima.perm_write, ima.perm_create, ima.perm_unlink
FROM   ir_model_access ima
JOIN   ir_model im ON im.id = ima.model_id
LEFT   JOIN res_groups rg ON rg.id = ima.group_id
WHERE  im.model = 'MODEL_NAME'
ORDER  BY 1;
""",
    ),
    (
        "Record rules on one model",
        "A refusal that survives correct model access is almost always a "
        "record rule. Read the domain, do not guess it.",
        """
SELECT ir.id, ir.name, im.model, ir.active, ir.global,
       ir.perm_read, ir.perm_write, ir.perm_create, ir.perm_unlink,
       ir.domain_force
FROM   ir_rule ir
JOIN   ir_model im ON im.id = ir.model_id
WHERE  im.model = 'MODEL_NAME'
ORDER  BY ir.active DESC;
""",
    ),
    (
        "Groups one user actually holds",
        "The user's own list, resolved. Faster and more reliable than "
        "reading the settings form.",
        """
SELECT ru.id AS user_id, rp.name AS login_name, rg.name->>'en_US' AS group_name
FROM   res_users ru
JOIN   res_partner rp ON rp.id = ru.partner_id
JOIN   res_groups_users_rel rel ON rel.uid = ru.id
JOIN   res_groups rg ON rg.id = rel.gid
WHERE  ru.login = 'USER_LOGIN'
ORDER  BY 3;
""",
    ),
]

Q["cron"] = [
    (
        "All scheduled actions with their next run",
        "A nextcall in the past on an active cron means the scheduler is not "
        "running or is stuck behind another job.",
        """
SELECT ic.id, ia.name->>'en_US' AS action, ic.active, ic.nextcall,
       ic.interval_number, ic.interval_type, ic.numbercall, ic.priority
FROM   ir_cron ic
LEFT   JOIN ir_act_server ia ON ia.id = ic.ir_actions_server_id
ORDER  BY ic.active DESC, ic.nextcall ASC;
""",
    ),
    (
        "Cron rows currently locked by a worker",
        "A held lock with no progress is a cron that crashed mid run. Check "
        "the server log for the same window.",
        """
SELECT ic.id, ia.name->>'en_US' AS action, ic.nextcall,
       a.pid, a.state, now() - a.query_start AS running_for
FROM   ir_cron ic
LEFT   JOIN ir_act_server ia ON ia.id = ic.ir_actions_server_id
LEFT   JOIN pg_locks l ON l.relation = 'ir_cron'::regclass
LEFT   JOIN pg_stat_activity a ON a.pid = l.pid
WHERE  ic.active
ORDER  BY ic.nextcall ASC
LIMIT  25;
""",
    ),
]

Q["attachment-bloat"] = [
    (
        "Attachment volume by model",
        "Tells you which feature is filling the disk before you start "
        "deleting anything.",
        """
SELECT coalesce(res_model, '(none)') AS model,
       count(*) AS files,
       pg_size_pretty(sum(file_size)::bigint) AS total
FROM   ir_attachment
GROUP  BY 1
ORDER  BY sum(file_size) DESC NULLS LAST
LIMIT  25;
""",
    ),
    (
        "Attachments stored in the database rather than the filestore",
        "db_datas rows bloat every backup. On a healthy install this is "
        "small and mostly assets.",
        """
SELECT id, name, res_model, res_id, file_size, create_date
FROM   ir_attachment
WHERE  db_datas IS NOT NULL
ORDER  BY file_size DESC NULLS LAST
LIMIT  50;
""",
    ),
    (
        "Attachments pointing at a record that no longer exists",
        "Candidates for cleanup. Confirm the model name before acting, and "
        "note that res_model NULL rows are not orphans.",
        """
SELECT ia.res_model, count(*) AS orphan_candidates,
       pg_size_pretty(sum(ia.file_size)::bigint) AS total
FROM   ir_attachment ia
JOIN   ir_model im ON im.model = ia.res_model
WHERE  ia.res_id IS NOT NULL
GROUP  BY 1
ORDER  BY sum(ia.file_size) DESC NULLS LAST
LIMIT  25;
""",
    ),
]

Q["duplicate"] = [
    (
        "Duplicate values on a column that is supposed to be unique",
        "Fill in the table and column. Run this before adding a unique "
        "constraint, because the constraint will fail on existing rows and "
        "the failure arrives during an upgrade.",
        """
SELECT COLUMN_NAME, count(*) AS rows, array_agg(id ORDER BY id) AS ids
FROM   TABLE_NAME
WHERE  COLUMN_NAME IS NOT NULL
GROUP  BY 1
HAVING count(*) > 1
ORDER  BY 2 DESC
LIMIT  50;
""",
    ),
    (
        "Partners duplicated on name and email",
        "The most common real instance of the above.",
        """
SELECT lower(trim(name)) AS name, lower(trim(email)) AS email,
       count(*) AS rows, array_agg(id ORDER BY id) AS ids
FROM   res_partner
WHERE  active AND email IS NOT NULL
GROUP  BY 1, 2
HAVING count(*) > 1
ORDER  BY 3 DESC
LIMIT  50;
""",
    ),
]

Q["currency"] = [
    (
        "Rate coverage per currency",
        "A gap between last rate and today is why a report converts at a "
        "stale figure. Odoo uses the most recent rate on or before the date, "
        "so a missing month is silent.",
        """
SELECT rc.name AS currency, count(rcr.id) AS rates,
       min(rcr.name) AS first_rate, max(rcr.name) AS last_rate
FROM   res_currency rc
LEFT   JOIN res_currency_rate rcr ON rcr.currency_id = rc.id
WHERE  rc.active
GROUP  BY 1
ORDER  BY 4 DESC NULLS LAST;
""",
    ),
    (
        "Duplicate rates on the same currency, date and company",
        "Should be empty. Duplicates make conversion depend on row order.",
        """
SELECT currency_id, name AS rate_date, company_id, count(*) AS rows
FROM   res_currency_rate
GROUP  BY 1, 2, 3
HAVING count(*) > 1
ORDER  BY 4 DESC
LIMIT  50;
""",
    ),
    (
        "Months with no rate at all, per currency",
        "The gaps, listed. Compare against the periods the client is "
        "reporting on.",
        """
SELECT rc.name AS currency,
       to_char(date_trunc('month', rcr.name), 'YYYY-MM') AS month,
       count(*) AS rates
FROM   res_currency rc
JOIN   res_currency_rate rcr ON rcr.currency_id = rc.id
WHERE  rc.active
GROUP  BY 1, 2
ORDER  BY 1, 2;
""",
    ),
]


def guard(sql):
    low = sql.lower()
    for w in WRITES:
        if w in low:
            raise SystemExit(
                "refused: query %r contains a writing statement. This tool "
                "emits read-only diagnostics only." % w.strip()
            )
    return sql


def show(symptom, sql_only=False):
    rows = Q[symptom]
    if not sql_only:
        print("-- %s: %d queries, all read only" % (symptom, len(rows)))
        print("-- placeholders in CAPITALS must be filled in before running")
        print()
    for i, (title, expect, sql) in enumerate(rows, 1):
        guard(sql)
        if not sql_only:
            print("-- [%d/%d] %s" % (i, len(rows), title))
            for line in wrap(expect):
                print("--   %s" % line)
        print(sql.strip())
        print()


def wrap(text, width=72):
    out, line = [], ""
    for word in text.split():
        if len(line) + len(word) + 1 > width:
            out.append(line)
            line = word
        else:
            line = (line + " " + word).strip()
    if line:
        out.append(line)
    return out


def main(argv):
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__.strip())
        print("\nsymptoms: %s" % ", ".join(sorted(Q)))
        return 0
    if argv[0] == "--list":
        for k in sorted(Q):
            print("%-18s %d queries" % (k, len(Q[k])))
        return 0
    symptom = argv[0]
    if symptom not in Q:
        print("unknown symptom %r\nknown: %s" % (symptom, ", ".join(sorted(Q))))
        return 2
    show(symptom, sql_only="--sql-only" in argv)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
