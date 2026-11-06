-- Valuation layers that carry value but no accounting entry.
-- On automated valuation this should be empty. Rows here are usually the
-- whole of the gap from 01. Read only.

\set company 1

SELECT svl.id, svl.create_date::date AS created,
       pt.name->>'en_US'  AS product,
       svl.quantity, svl.value, svl.description
FROM   stock_valuation_layer svl
JOIN   product_product pp ON pp.id = svl.product_id
JOIN   product_template pt ON pt.id = pp.product_tmpl_id
WHERE  svl.company_id = :company
  AND  svl.account_move_id IS NULL
  AND  svl.value <> 0
ORDER  BY abs(svl.value) DESC
LIMIT  200;
