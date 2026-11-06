-- Outgoing valuation by month, so the client can see which period moved.
-- Compare against their own COGS figure per month. Read only.

\set company 1

SELECT to_char(date_trunc('month', svl.create_date), 'YYYY-MM') AS period,
       count(*)                                  AS layers,
       round(sum(svl.quantity)::numeric, 2)      AS qty_out,
       round(sum(-svl.value)::numeric, 2)        AS cogs,
       count(*) FILTER (WHERE svl.account_move_id IS NULL) AS without_entry
FROM   stock_valuation_layer svl
WHERE  svl.company_id = :company
  AND  svl.quantity < 0
GROUP  BY 1
ORDER  BY 1;
