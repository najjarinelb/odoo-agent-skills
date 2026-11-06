---
name: mna-qweb
description: >-
  Write and lint QWeb PDF reports for Odoo, catching the things that only
  show up in the rendered PDF. Use for "custom report", "invoice layout",
  "PO report", "the report is cut off", "add our logo", "report in Arabic",
  or any QWeb or paper format work.
---

# mna-qweb

A QWeb report looks correct in the browser and wrong in the PDF, because wkhtmltopdf is not the
browser. Everything in this skill is about that gap.

```bash
python3 qweb_lint.py report_template.xml
python3 qweb_lint.py /path/to/module/report/
```

## Before you write

1. Read `~/.claude/odoo/context.md` for the version. The external layout and its hooks changed
   between versions, and a template inheriting the wrong one renders without a header.
2. Ask for the current PDF, not a description of it. A client saying the total is wrong and a PDF
   showing the total in the wrong column are different tickets.
3. Ask whether it must render right to left. Arabic reports are not a styling variant, they change
   the layout decisions you make, and retrofitting is more work than starting with it.

## Rules the linter checks, and why

- **`t-out`, never `t-esc` or `t-raw`.** `t-esc` is superseded and `t-raw` was removed.
- **Monetary fields need `t-options`.** Printing a monetary field without the currency widget gives
  a bare number with no symbol and no rounding, which on an invoice is a defect.
- **The report action needs a paper format.** Without one it falls back to a default and margins
  silently differ from whatever was designed.
- **No hardcoded company name, address or logo.** These must come from the company record, or the
  report breaks the moment a second company exists. On a multi company database this is the single
  most common cause of a wrong PDF.
- **Inherit `web.external_layout`** rather than rebuilding a header. A hand built header loses the
  company block, the watermark and the layout setting the client chose.
- **Fixed pixel widths and absolute positioning.** These are the usual cause of content cut off at
  the page edge. Tables and percentages survive the PDF engine, pixels do not.
- **Every visible string needs to be translatable.** A string baked into the template cannot be
  translated into Arabic later without editing the template again.

## Right to left

When the report must render in Arabic:

- Set the direction on the document body, not on individual elements.
- Mirror the layout, do not merely align text to the right. Totals, logos and the signature block
  all move.
- Check number and date formatting separately. Direction and locale are different settings and
  fixing one does not fix the other.
- Render the PDF and look at it. There is no substitute for this step.

## The one thing that settles it

Render the PDF. Not the preview, the PDF. Every structural change gets rendered before it is called
done, because the browser and wkhtmltopdf disagree in exactly the ways that matter.

## The gate

This writes templates and reports lint findings. It installs nothing and renders nothing itself.
Every run ends with: **render the PDF and compare it against the one the client sent.**
