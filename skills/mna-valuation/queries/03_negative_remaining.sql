-- Layers consumed below zero. This is what backdating produces, and it is
-- the usual cause of a COGS figure that cannot be traced to a cost.
-- Read only.

\set company 1

SELECT pt.name->>'en_US' AS product,
       count(*)                                   AS bad_layers,
       round(sum(svl.remaining_qty)::numeric, 4)  AS remaining_qty,
       round(sum(svl.remaining_value)::numeric, 2) AS remaining_value,
       min(svl.create_date)::date                 AS first_seen,
       max(svl.create_date)::date                 AS last_seen
FROM   stock_valuation_layer svl
JOIN   product_product pp ON pp.id = svl.product_id
JOIN   product_template pt ON pt.id = pp.product_tmpl_id
WHERE  svl.company_id = :company
  AND  svl.remaining_qty < 0
GROUP  BY 1
ORDER  BY 3 ASC
LIMIT  100;
