# Changelog

Version history of the standalone web app. Archived snapshots live in
`versions/`; `index.html` is the current release (= v6).

## v9 — persist done-checks with the run
- Done-checks are now saved inside the run, so **Save run / Open run** and the
  unsaved-session **recovery banner** restore your pipetting progress.
- A plain page reopen still starts fresh (checks cleared); they only come back
  when an earlier run is loaded.

## v8 — dilution tubes + done checklist
- The standalone dilution calculator now shows a **tube per sample** (DNA vs
  buffer as proportional layers; one mini-tube per serial step) with volumes.
- Added a **Done** checklist: tick off each dilution tube and each pooling-table
  row as you pipette, with a live "✓ X / N done" progress badge.

## v7 — tube pool preview
- Added a **Plate / Tube** toggle to the pool preview card.
- New dynamic **single-tube graphic**: an Eppendorf that fills with one
  translucent, labeled colour band per sample (bottom = first sample), with a
  matching colour legend — a visual of what goes into a manually- or
  robot-pooled tube. Updates live as samples are added.

## v6 — section + whole-page clearing
- Bottom **New / clear** button now clears the *entire* page, including the
  standalone dilution section.
- Added a **Clear section** button to each input section.

## v5 — multi-sample dilution list
- Standalone dilution calculator became a **sample list**: per-sample stock with
  shared target/volume defaults, combined dilution table, per-sample serial
  steps, total diluent for the batch, and a downloadable list CSV.
- Relabeled the well limit to "Max well/tube capacity".

## v4 — serial dilution fixes + standalone calculator
- **Fixed** dilution/pooling execution order: dilution is now a separate ordered
  `Dilution.csv` that runs first (robot mixes each well); pooling then sources
  from the diluted wells. (Previously dilution rows were merged into the pooling
  worklists, which the robot couldn't execute in the right order.)
- Unified the max-well default to 200 µL.
- Added the standalone dilution calculator (single sample), nM and ng/µL.
- Fixed a `fmt()` bug that stripped trailing zeros from integers (2500 → 25).

## v3 — serial dilution
- Auto serial-dilution steps for over-concentrated samples (equal split factor,
  chained wells, editable destination wells).

## v2 — fresh-start + recovery
- Blank start on every open (no silent auto-restore), with a dismissible
  recovery banner for unsaved previous sessions.
- Save-run button, unsaved-changes guard, and a fix so exported CSVs re-import
  cleanly (parameters block no longer parsed as samples).

## v1 — enhanced app
- Plate map, workflow modes, min-volume solver, post-rounding CV report, tip
  selection, run metadata, direct-nM input, replicate-read averaging, embedded
  PDF guide.

## v0 — original
- `pool.html`: first browser version (equimolar pooling + epMotion CSV export),
  mirroring the Python tools.
