# Changelog

Version history of the standalone web app. Archived snapshots live in
`versions/`; `index.html` is the current release (= v21).

## v21 — choose the output well everywhere + full guidance
- **Dilute gained a Plate view** (toggle with Tube view) showing stock plate → diluted plate,
  plus per-row **In well** and **Out well**. The epMotion dilution export now uses those wells
  instead of auto-assigning them.
- **Pool (Plate layout) gained a per-sample "Out well"**, so a sample can be normalized into
  any well of the output plate; `DNA.csv`/`Buffer.csv`, the worksheet, the inputs CSV, the
  blank template and instrument-CSV import all carry it.
- So all three tasks now let you pick exactly where each sample lands, and the live graphic
  and exported worklists agree.
- **Fixed:** the in-app user guide could never be opened (nothing un-hid the panel) — the
  header button now opens it. Dilute inputs are now saved with the run like the other tabs.
  Removed dead code (the old tube-graphic renderer and the retired Plate/Tube toggle).
- **Guidance rewritten:** the in-app guide now has nine sections covering all three tabs
  step by step, and both PDF guides were regenerated with full how-to coverage (the detailed
  one is re-embedded for the in-app download). README refreshed.

## v20 — transfer-aware graphics (source → destination, with volumes)
- Every preview now shows **where each sample goes and how much**:
  - **Pool** follows the Layout choice — **Tube** draws source plate → pool tube (with the
    pooled tube filling in layers, one per sample plus buffer); **Plate** draws source plate →
    output plate. The old manual Plate/Tube toggle is gone; the preview follows the layout.
  - **Normalize** draws library plate → normalized plate with the exact well mapping.
- Each graphic is paired with a **transfer list**: `S1 · A1 → A1 · 3.1 µL + 13.6 µL buffer`,
  and wells carry tooltips with their volume.
- **Normalize gained an optional "Output well"** per library (defaults to the same well), so a
  library can be moved — e.g. **A3 → D5** — and the exported DNA/Buffer worklists follow it.
- Fixed a repaint issue from the fixed-attachment background.

## v19 — fill animations + bolder task tabs
- **Fill animations:** tubes now fill from the bottom up (Dilute previews, dilution-result
  mini tubes, and the Pool single-tube graphic), and Normalize plate wells pop in with a
  staggered delay. The input→output arrow has a flowing dashed line.
- **Task tabs** are now clearly coloured sections — Pool (indigo), Normalize (teal), Dilute
  (amber) — each with a thick top accent, gradient fill when active, and a lift on hover, so
  they read as real tabs instead of blending into the page.
- Respects `prefers-reduced-motion`.

## v18 — live Dilute tubes + visual polish
- **Dilute** now shows a live **virtual tube** per sample as you type — a proper glass tube
  with teal DNA (stock) over light-blue buffer, sized to the real ratio, with volume labels
  and a legend. Incomplete rows show a faint empty tube prompting for target/volume.
- Global polish pass: soft gradient background, gradient primary buttons with hover lift,
  focus rings on inputs, and consistent card shadows.

## v17 — live section graphics + cleaner Pool actions
- **Normalize** now shows a live **two-plate graphic** (library input plate → normalized
  output plate) with each library colour-coded in its well on both plates, an arrow, and a
  legend — so you can see which sample goes where as you type.
- **Dilute** now updates its tube preview and table **live** as you enter values (no need to
  click Calculate first).
- Removed the redundant top "Choose your workflow" cards (they just re-triggered the bottom
  buttons). The Pool tab now has a short lead line explaining its three distinct actions —
  Calculate molarities, Quick pool table, Generate worklists — which live once in the action bar.

## v16 — Normalize inputs saved with the run
- Normalize inputs (unit, target, volume, and the library rows) are now part of
  **Save run / Open run** and the unsaved-session recovery banner. As with the rest of
  the app, a plain page reload still starts blank — Normalize only comes back when a run
  is saved/restored. **New / clear** now resets the Normalize tab too.

## v15 — tabbed redesign + dedicated Normalize task
- Reorganized the app into three clear tabs — **Pool**, **Normalize**, **Dilute** — so it's
  obvious which task is which and where to enter details. Each tab is self-contained.
- New **Normalize** task (plate → plate): enter each library's well + concentration (nM or
  ng/µL) and a target; exports `Normalization_DNA.csv` (library → output plate, same well) +
  `Normalization_Buffer.csv` (buffer from the reservoir at position "1"), matching the
  Eppendorf normalization template exactly. Over-concentrated libraries are flagged to
  pre-dilute first.

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
