# Offline report-choice exercise (synthetic)

Read the published QUICKSTART.md first. Use only the bundled invented CSVs.
Use this worksheet to practice choosing reports and interpreting batch results.
Do not consult ANSWER-KEY.md until recording your answers. No timing target.

1. You need only counts, without record positions. Which report do you choose?
2. You must locate changed columns/record positions and retain input hashes.
   Which report do you choose? Does it show old/new cell values?
3. Run the packaged before/after example with --check and your first choice.
   Predict its status and four change counts before executing.
4. Review three pairs in order: before/before; before/after;
   before/evaluation/duplicate-key.csv, with key id. Predict per-pair and
   aggregate statuses, and which pairs produce JSON reports. Does the aggregate
   status establish that all pairs are equal or that every pair failed?
5. Put the invalid pair first, then changed, then equal. Predict the aggregate
   status and whether processing reaches the equal pair.
6. Locate the changed status cell in the detailed report. What does record 1
   mean? Where do you inspect the actual old/new values? How do you rerun a
   batch without overwriting its saved evidence?

The first two tasks concern mode choice; the remaining tasks concern reading
actual outputs. Record answers and confusing wording locally. Never submit private CSVs or reports in public feedback.
