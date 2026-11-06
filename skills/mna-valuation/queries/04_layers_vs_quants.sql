-- Valued quantity against on-hand quantity, per product.
-- A gap here is a data problem and not an accounting one, so it is fixed
-- before anything is posted. Read only.

\set company 1

WITH valued AS (
    SELECT svl.product_id,
           round(sum(svl.quantity)::numeric, 4) AS valued_qty,
           round(sum(svl.value)::numeric, 2)    AS valued_value
    FROM   stock_valuation_layer svl
    WHERE  svl.company_id = :company
    GROUP  BY 1
),
onhand AS (
    SELECT sq.product_id,
           round(sum(sq.quantity)::numeric, 4) AS onhand_qty
    FROM   stock_quant sq
    JOIN   stock_location sl ON sl.id = sq.location_id
    WHERE  sl.usage = 'internal'
      AND  sq.company_id = :company
    GROUP  BY 1
)
SELECT pt.name->>'en_US' AS product,
       coalesce(v.valued_qty, 0)  AS valued_qty,
       coalesce(o.onhand_qty, 0)  AS onhand_qty,
       coalesce(v.valued_qty, 0) - coalesce(o.onhand_qty, 0) AS qty_gap,
       coalesce(v.valued_value, 0) AS valued_value
FROM   valued v
FULL   JOIN onhand o ON o.product_id = v.product_id
JOIN   product_product pp ON pp.id = coalesce(v.product_id, o.product_id)
JOIN   product_template pt ON pt.id = pp.product_tmpl_id
WHERE  round(coalesce(v.valued_qty, 0) - coalesce(o.onhand_qty, 0), 4) <> 0
ORDER  BY abs(coalesce(v.valued_qty, 0) - coalesce(o.onhand_qty, 0)) DESC
LIMIT  200;
