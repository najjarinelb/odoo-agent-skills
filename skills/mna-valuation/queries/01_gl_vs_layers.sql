-- The gap, as one number per stock account, as of a date.
-- Everything else in this folder explains this output.
-- Set the company and the date before running. Read only.

\set company 1
\set asof '2026-12-31'

WITH gl AS (
    SELECT aml.account_id,
           round(sum(aml.debit - aml.credit)::numeric, 2) AS gl_balance
    FROM   account_move_line aml
    JOIN   account_move am ON am.id = aml.move_id
    JOIN   account_account aa ON aa.id = aml.account_id
    WHERE  am.state = 'posted'
      AND  aml.company_id = :company
      AND  am.date <= :'asof'
      AND  aa.id IN (
             SELECT DISTINCT pc.property_stock_valuation_account_id
             FROM   product_category pc
             WHERE  pc.property_stock_valuation_account_id IS NOT NULL
           )
    GROUP  BY 1
),
layers AS (
    SELECT pc.property_stock_valuation_account_id AS account_id,
           round(sum(svl.value)::numeric, 2)      AS layer_value
    FROM   stock_valuation_layer svl
    JOIN   product_product pp ON pp.id = svl.product_id
    JOIN   product_template pt ON pt.id = pp.product_tmpl_id
    JOIN   product_category pc ON pc.id = pt.categ_id
    WHERE  svl.company_id = :company
      AND  svl.create_date::date <= :'asof'
    GROUP  BY 1
)
SELECT aa.code, aa.name->>'en_US' AS account,
       coalesce(gl.gl_balance, 0)   AS gl_balance,
       coalesce(l.layer_value, 0)   AS layer_value,
       coalesce(gl.gl_balance, 0) - coalesce(l.layer_value, 0) AS gap
FROM   account_account aa
LEFT   JOIN gl ON gl.account_id = aa.id
LEFT   JOIN layers l ON l.account_id = aa.id
WHERE  gl.account_id IS NOT NULL OR l.account_id IS NOT NULL
ORDER  BY abs(coalesce(gl.gl_balance, 0) - coalesce(l.layer_value, 0)) DESC;
