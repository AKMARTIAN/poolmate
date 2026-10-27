# PoolMate

**PoolMate** is a browser-based equimolar pooling helper for planning **library
pools** and **dilutions**, and generating the Eppendorf **epMotion** worklist
CSVs (`DNA.csv` / `Buffer.csv`). Everything runs locally in the browser — **no
install, no server, and no data ever leaves your machine** (entries are kept
only in your browser's local storage).

## ▶ Use it now

**https://akmartian.github.io/poolmate/**

Open the link in any modern browser (Chrome, Edge, Safari, Firefox) on Windows,
macOS, or Linux. Nothing to install.

## What it does

PoolMate has five self-contained tasks, each with a live graphic showing **where every
sample goes and how much**:

- **Pool** — combine libraries into one tube, or normalize each into its own well. Enter
  concentrations (ng/µL + fragment size, or direct nM, with replicate-read averaging) and a
  target (nM or fmol); PoolMate computes the equal-mole transfer per sample, the buffer
  top-up, and a post-rounding equimolar-deviation (CV%) check, then exports the epMotion
  `DNA.csv` and `Buffer.csv`. A per-sample **share** makes a pool deliberately uneven when you
  want it: 1 everywhere is equimolar, 2 gives that library twice the representation, 0 leaves
  it out.
- **Normalize** — dilute every library to one common concentration, plate → plate. Set a
  target in nM or ng/µL and a volume per well; each library can optionally be routed to a
  different **output well** (e.g. A3 → D5).
- **Dilute** — dilute one sample or a whole list. **Tube view** gives a virtual tube per
  sample with a Done checklist for bench work; **Plate view** gives a plate → plate map with
  per-sample in/out wells. Every parameter (target, final volume, min transfer, max capacity,
  rounding) has a shared default that can be overridden per row.
- **Serial dilution** — when a sample is too concentrated to reach the target in one step,
  the steps are laid out automatically. For pooling this is exported as an ordered
  `Dilution.csv` that runs first.
- **Load** — work out what to put on a flow cell. Pick Oxford Nanopore or Illumina and a
  flow cell / kit preset, enter one pool or several pools to combine (with a per-pool share),
  and PoolMate gives the µL of each pool plus the bench steps: the ONT loading mix (with the
  Elution Buffer top-up), or the Illumina dilution steps down to the loading pM. Presets are
  vendor starting points and every value is editable.
- **Pool plan** — every pooling run also writes a small `<prefix>_pool.poolplan.json`. Take it
  to the **[epMotion Protocol Builder](https://akmartian.github.io/poolmate/builder/)** (Pool tab
  → *Import plan / CSV*) and it writes a ready-to-run `.export52` with the pre-dilutions, the
  pooling and the mixing in a single protocol — no worklist CSVs to load at the instrument.
  The builder exports the same format, and the *Import CSV* button here reads it back.
- **Quality of life** — platform presets (Illumina / ONT), run metadata, print / save to PDF,
  save & reopen runs as JSON, instrument CSV import, auto-named downloads, per-section and
  whole-page clear, and a fresh blank start each time (with one-click recovery of an unsaved
  session).

> Dilution and pooling are always **separate robot runs** when you drive the instrument with
> these worklist CSVs: pooling must draw from wells that have already been diluted *and mixed*.
> A protocol built from a pool plan does both in one run, because it mixes each dilution
> itself before anything is pooled.

> ⚠️ The built-in platform presets are vendor starting points. **Confirm all
> volumes and loading concentrations against your own kit / instrument SOP
> before running anything on the robot.**

## Repository layout

| Path | What it is |
|------|------------|
| `index.html` | The live web app (this is what GitHub Pages serves). |
| `builder/` | A page about the **[epMotion Protocol Builder](https://akmartian.github.io/poolmate/builder/)**, the companion program that turns a pool plan into a robot protocol. The builder itself lives in a private lab repository and the page links to it. |
| `versions/` | Archived snapshots of each working version (`pool.html` → `pool_enhanced_v9.html` → `PoolMate_v10.html`). The newest snapshot mirrors `index.html` and serves as a fallback. |
| `Buffer.csv`, `DNA.csv` | The original Eppendorf epMotion worklist templates this matches. |
| `*.pdf` | User guides. |

## Want to change it?

PoolMate is a single self-contained file (`index.html` — HTML, CSS, and vanilla
JS, no build step). To customize it for your own lab, **fork the repository** and
edit your copy; pull requests are welcome but not required.

## License

MIT — see `LICENSE`.
