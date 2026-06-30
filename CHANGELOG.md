# Changelog

Version history of the standalone web app. Archived snapshots live in
`versions/`; `index.html` is the current release (= v14).

## v14 — run dilutions on the pooling script
- The standalone dilution calculator can now **export epMotion worklists**
  (`dilution_DNA.csv` = stock, `dilution_Buffer.csv` = diluent) in the same Rack-1
  format as the pooling templates, so a single-step dilution runs on the existing
  pooling script as a separate run. Samples are auto-assigned wells in list order;
  serial (multi-step) dilutions are excluded with a warning (each step needs its own
  run). Buffer is drawn from Rack 1, position "1", matching the Eppendorf templates.

## v13 — clearer Plate / Tube layout labels
- Renamed the layout options to **"Tube — pool everything into one tube"** and
  **"Plate — each sample in its own well"** (the old `one-tube` / `normalize` values
  are unchanged under the hood). The Plate layout reproduces the Eppendorf
  DNA.csv/Buffer.csv template structure (all Rack 1); the Tube layout pools into a
  separate destination rack.
- Reworded the Buffer-rack help: it should normally match the source rack, since many
  fixed pooling scripts only use racks 1–2.

## v12 — dedicated buffer rack
- Added a **Buffer rack number** field so buffer/diluent can sit in its own tube or
  reservoir on a separate deck position instead of a well of the sample plate. The
  Buffer worklist (and the pre-dilution diluent) now source from that rack; it
  defaults to the source rack, so existing runs are unchanged.

## v11 — PoolMate user guides
- Regenerated the embedded **detailed PDF guide** and the standalone guide PDFs
  under the PoolMate name (`PoolMate_User_Guide.pdf`,
  `PoolMate_Detailed_User_Guide.pdf`), refreshed to cover the per-row dilution
  overrides and the mass-mode counter. Removed the old `epMotion_*` guide PDFs.

## v10 — PoolMate rebrand + per-row dilution overrides
- Renamed the app to **PoolMate** (UI title, header, user guide, and generated
  worklist header). References to **epMotion** are kept where they mean the
  actual robot or its worklist files.
- The standalone dilution calculator's **min transfer, max well/tube capacity,
  and rounding** are now **per-row overrides** that fall back to shared
  defaults — joining target and final volume, which were already per-row.

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
