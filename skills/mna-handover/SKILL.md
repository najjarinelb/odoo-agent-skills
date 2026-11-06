---
name: mna-handover
description: >-
  Write the handover document for a delivered Odoo module or customization,
  aimed at the next consultant rather than at the client's filing cabinet.
  Use for "document this module", "handover", "write the UAT notes", "what
  did we change", or closing out a delivery.
---

# mna-handover

Most Odoo handover documents are written for whoever signs them and read by nobody. The person who
actually needs this document is the consultant who inherits the module in eighteen months with no
context, and that is who it gets written for.

That person has one question: **what will surprise me?** Answer that and the rest is optional.

## Before writing

1. Read `~/.claude/odoo/context.md` for the version, the deployment and the delivery format.
2. Read the actual code. Not the ticket, not the specification, the code as delivered. The
   specification describes what was agreed and the code describes what shipped, and the gap between
   them is the most valuable paragraph in the document.
3. List the files that changed. If this is not known, it needs to be established before anything is
   written, because a handover that omits a changed file is worse than none.

## What goes in, in this order

`references/template.md` holds the structure. The order is deliberate: a reader who stops after two
sections should still have the dangerous parts.

1. **What it does**, in two sentences, in the client's own words.
2. **What will surprise you.** The non-obvious decisions, the constraints that forced them, and
   anything that looks like a mistake but is not. This section exists so the next person does not
   "fix" something deliberate.
3. **Files changed**, with one line each on why.
4. **Configuration it depends on.** Settings, categories, journals, groups. A module that works
   only when a category has a specific costing method must say so, because that is how it breaks.
5. **What it does not do.** Scope that was discussed and excluded. This prevents the same
   conversation a year later and protects the original decision.
6. **How to verify it still works**, as steps someone can run without asking anybody.
7. **Known limitations and the conditions that trigger them.**

## Two documents, not one

The client and the next consultant need different things, and merging them serves neither.

- **Client facing**: what changed, how to use it, how to verify it. Professional register. No table
  names, no field names, no file paths.
- **Technical**: everything above. Written for someone reading the code with the document open.

Ask which one is wanted. If the answer is both, write both, and do not let the client version
inherit the technical detail.

## Never do these

- Never claim a test that was not run. If UAT covered three of five cases, the document says three.
- Never describe intended behaviour as verified behaviour.
- Never leave a known issue out because the delivery is being signed off. It will be found, and
  found later costs more than disclosed now.

## The gate

This writes a document and nothing else. Every run ends with the question: **is there anything in
the module that would surprise the next person, which is not in section two?**
