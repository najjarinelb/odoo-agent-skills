---
name: mna-diagnose
description: >-
  Produce the read-only psql and shell commands that prove what is actually
  wrong in an Odoo database before any code is written. Use for "why is this
  wrong", "the numbers don't match", "this module won't install", "it's
  slow", a pasted traceback, or any Odoo bug whose cause is not yet known.
---

# mna-diagnose

Most wrong Odoo code is written against a guess about data. The guess is usually reasonable and
usually wrong, and the cost lands on a client at month end.

This skill does not write a fix. It writes the commands that find the cause.

```bash
python3 dx.py --list
python3 dx.py stock-valuation
python3 dx.py invoice-mismatch --module account
```

## The rule

**Do not write code until the output of a diagnostic is in hand.** Not a plausible explanation of
the symptom, the actual rows. If the user asks for a fix before any output exists, give them the
diagnostic first and say plainly that the fix comes after the output.

This holds even when the cause looks obvious. An obvious cause that turns out to be wrong costs
more than one round trip of commands.

## Before you run anything

1. Read `~/.claude/odoo/context.md`. It carries the versions in play, the deployment for each, and
   how to reach a shell and a psql prompt. If it does not exist, ask for the version and the
   deployment before emitting a single command, because the table and column names differ.
2. Confirm which database. Never assume production. Ask.
3. Everything this skill emits is **read only**. `dx.py` refuses to print anything that writes. If
   a fix needs an UPDATE, that is a separate decision the user makes with the output in front of
   them, not something a diagnostic hands over quietly.

## What it covers

`dx.py --list` prints the symptoms it knows. Each one emits a small ordered set of queries, with a
line above each saying what the output will tell you and what a healthy result looks like.

Symptoms: stock valuation against the accounting entries, orphaned or negative quants, invoice and
journal entry mismatch, module stuck in a bad install state, slow queries and missing indexes,
access rights refusals, dead or stuck crons, attachment and filestore bloat, duplicate records on a
supposedly unique key, and currency rate gaps.

## Reading the output

State what the rows mean before proposing anything. If the output contradicts what the user
reported, say so. A client describing a symptom is describing what they noticed, not what happened.

If the output is empty, that is a finding. An empty result on a mismatch query means the mismatch is
somewhere else, and the next step is a different query, not a fix aimed at the original theory.

## Then, and only then

Write the **minimum** change that addresses the cause the output showed. Minimal diff, no inline
comments, only the files that changed. If the cause is data rather than code, say so rather than
writing code to paper over it.

## The gate

Nothing here modifies a database. Every run ends the same way: **here is what the output has to say
before I write anything.**
