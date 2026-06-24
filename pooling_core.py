#!/usr/bin/env python3
"""
Shared core for the epMotion equimolar pooling helper.

Both the terminal app (pool.py) and the GUI (pool_gui.py) import everything
from here so the science lives in exactly one place.

Molarity conversion used throughout:
    nM = (conc_ng_per_uL * 1e6) / (660 * fragment_size_bp)
(660 g/mol = average MW of one dsDNA base pair; 1 nM = 1 fmol/uL.)
"""

import csv
import datetime
import json
import os

# --------------------------------------------------------------------------- #
#  PLATFORM PRESETS -- real loading guidance, all overridable at run time.     #
#                                                                              #
#  The number the tool actually uses to pool is `target_nm` (the molar         #
#  concentration the pool is normalized to) over `volume_ul`. `loading` and    #
#  `note` are reference text shown to the user. EDIT IF YOUR SOP DIFFERS.      #
# --------------------------------------------------------------------------- #

PRESETS = {
    "illumina": {
        "label": "Illumina",
        "default": "pool_4nM",
        "options": {
            "pool_4nM": {
                "target_nm": 4.0,
                "volume_ul": 50.0,
                "loading": "4 nM pooling stock",
                "note": (
                    "Illumina standard: pool/normalize libraries to a 4 nM "
                    "stock for denature & dilute (preferred starting range "
                    "2-4 nM). Final on-instrument loading is a SEPARATE "
                    "downstream dilution and is instrument-specific: MiSeq & "
                    "NextSeq 500/550 ~20 pM (standard normalization); NovaSeq "
                    "6000 ~300 pM (from 1.5 nM); NovaSeq X / X Plus ~300 pM; "
                    "iSeq 100 denatures onboard from ~1 nM."
                ),
            },
            "pool_2nM": {
                "target_nm": 2.0,
                "volume_ul": 50.0,
                "loading": "2 nM pooling stock",
                "note": (
                    "2 nM stock -- low end of Illumina's 2-4 nM starting "
                    "range; useful for lower-yield library pools."
                ),
            },
            "iseq_1nM": {
                "target_nm": 1.0,
                "volume_ul": 50.0,
                "loading": "1 nM (iSeq 100)",
                "note": (
                    "iSeq 100 workflow dilutes the library to ~1 nM; the "
                    "instrument then denatures onboard."
                ),
            },
        },
    },
    "ont": {
        "label": "Oxford Nanopore (SQK-LSK114 / R10.4.1)",
        "default": "simplex_50fmol",
        "options": {
            "simplex_50fmol": {
                "target_nm": round(50.0 / 12.0, 3),   # ~4.17 nM
                "volume_ul": 12.0,
                "loading": "50 fmol in 12 uL",
                "note": (
                    "High-output simplex: load 35-50 fmol of good-quality "
                    "library for >95% pore occupancy (MinION/PromethION "
                    "R10.4.1, SQK-LSK114). 50 fmol in 12 uL ~= 4.17 nM."
                ),
            },
            "duplex_20fmol": {
                "target_nm": round(20.0 / 12.0, 3),   # ~1.67 nM
                "volume_ul": 12.0,
                "loading": "20 fmol in 12 uL",
                "note": (
                    "Optimal duplex output: load 10-20 fmol so the flow cell "
                    "is neither under- nor over-loaded. 20 fmol in 12 uL "
                    "~= 1.67 nM."
                ),
            },
        },
    },
}


def list_platforms():
    return [(k, v["label"]) for k, v in PRESETS.items()]


def list_presets(platform):
    """Return [(key, loading_label)] for a platform, or [] if unknown."""
    plat = PRESETS.get(platform)
    if not plat:
        return []
    return [(k, o["loading"]) for k, o in plat["options"].items()]


def resolve_preset(platform, preset_key=None):
    """Return the preset option dict, falling back to the platform default."""
    plat = PRESETS.get(platform)
    if not plat:
        return None
    if not preset_key:
        preset_key = plat["default"]
    return plat["options"].get(preset_key)


# --------------------------------------------------------------------------- #
#  EPMOTION DECK / WORKLIST CONFIG -- adjust to your actual deck.              #
# --------------------------------------------------------------------------- #

TOOL = "TS_50"            # epMotion pipetting tool written into the worklist
SOURCE_RACK = 1          # rack holding the source library tubes/plate
DEST_RACK = 1            # rack holding the destination well(s)
BUFFER_SOURCE_RACK = 1   # rack holding the buffer reservoir
BUFFER_SOURCE_POS = "1"  # position of the buffer reservoir on its rack
POOL_WELL = "A1"         # destination well used in "one-tube" layout

MIN_PIPETTE_UL = 1.0     # warn if any transfer is below this (epMotion minimum)
DECIMALS = 1             # rounding for written volumes (epMotion accepts 0.1 uL)
MW_PER_BP = 660.0        # avg MW of one dsDNA base pair (g/mol)

_ROWS = "ABCDEFGH"
WELLS = [f"{r}{c}" for c in range(1, 13) for r in _ROWS]  # column-major, 96


# --------------------------------------------------------------------------- #
#  CORE CALCULATION                                                            #
# --------------------------------------------------------------------------- #

class PoolingError(Exception):
    """Raised when the requested pool cannot be made with the given inputs."""


def ng_per_ul_to_nm(conc_ng_ul, size_bp):
    """Convert mass concentration (ng/uL) to molar concentration (nM)."""
    return (conc_ng_ul * 1e6) / (MW_PER_BP * size_bp)


def _round(v):
    return round(v, DECIMALS)


def fmt_num(v):
    """Pretty-print a number: 4.0 -> '4', 4.17 -> '4.17', None -> ''."""
    if v in (None, ""):
        return ""
    try:
        f = float(v)
    except (TypeError, ValueError):
        return str(v)
    return str(int(f)) if f.is_integer() else str(f)


def preset_loading_label(state):
    """Human label for the chosen platform/preset, e.g. 'Illumina / 4 nM ...'."""
    plat = state.get("platform")
    if plat not in PRESETS:
        return None
    label = PRESETS[plat]["label"]
    preset = state.get("preset")
    if preset in PRESETS[plat]["options"]:
        return f"{label} / {PRESETS[plat]['options'][preset]['loading']}"
    return label


def auto_dirname(state, base_prefix="pool"):
    """
    A unique, hard-to-collide output folder name built from the pool
    concentration and a timestamp, e.g. 'pool_4nM_20260623-105730'. The
    seconds-resolution timestamp means repeated runs never overwrite.
    """
    conc = state.get("target_nm")
    tag = f"{fmt_num(conc)}nM" if conc not in (None, "") else "draft"
    ts = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    return f"{base_prefix}_{tag}_{ts}"


def missing_for_compute(state):
    """
    Inspect a project state dict and return a list of human-readable strings
    describing what still needs filling in before a worklist can be generated.
    Empty list == ready to compute. This drives the record-first workflow.
    """
    missing = []
    samples = state.get("samples") or []
    if not samples:
        missing.append("at least one sample")
    for i, s in enumerate(samples):
        tag = s.get("name") or f"sample {i + 1}"
        if s.get("conc") in (None, ""):
            missing.append(f"concentration for {tag}")
        if s.get("size") in (None, ""):
            missing.append(f"fragment size for {tag}")
    if state.get("target_nm") in (None, ""):
        missing.append("target pool concentration (nM)")
    if state.get("total_volume_ul") in (None, ""):
        missing.append("total pool volume (uL)")
    if state.get("layout") not in ("one-tube", "normalize"):
        missing.append("layout (one-tube or normalize)")
    return missing


def compute_pool(samples, target_nm, total_volume_ul, layout):
    """
    samples: list of dicts with keys name, conc (ng/uL), size (bp).
    Returns (samples_with_results, summary). Raises PoolingError if the target
    is unachievable. Mutates the sample dicts to add molarity_nm/sample_ul/
    buffer_ul.
    """
    n = len(samples)
    if n == 0:
        raise PoolingError("No samples provided.")
    if target_nm in (None, "") or float(target_nm) <= 0:
        raise PoolingError("Target pool concentration (nM) must be > 0.")
    if total_volume_ul in (None, "") or float(total_volume_ul) <= 0:
        raise PoolingError("Total pool volume (uL) must be > 0.")
    if layout not in ("one-tube", "normalize"):
        raise PoolingError("Layout must be 'one-tube' or 'normalize'.")

    target_nm = float(target_nm)
    total_volume_ul = float(total_volume_ul)

    for s in samples:
        if s.get("conc") in (None, "") or s.get("size") in (None, ""):
            raise PoolingError(
                f"Sample '{s.get('name')}' is missing a concentration or size.")
        if float(s["conc"]) <= 0 or float(s["size"]) <= 0:
            raise PoolingError(
                f"Sample '{s.get('name')}' has a non-positive conc or size.")
        s["conc"] = float(s["conc"])
        s["size"] = float(s["size"])
        s["molarity_nm"] = ng_per_ul_to_nm(s["conc"], s["size"])

    molarities = [s["molarity_nm"] for s in samples]
    m_min = min(molarities)
    harmonic_mean = n / sum(1.0 / m for m in molarities)

    # Equal moles per sample. 1 nM == 1 fmol/uL.
    fmol_per_sample = target_nm * total_volume_ul / n

    if layout == "normalize":
        max_target = m_min
        limit_desc = (f"lowest sample molarity ({m_min:.2f} nM); the per-well "
                      f"volume cannot hold enough of the most dilute library")
    else:  # one-tube
        max_target = harmonic_mean
        limit_desc = f"harmonic mean of sample molarities ({harmonic_mean:.2f} nM)"

    if target_nm > max_target + 1e-9:
        raise PoolingError(
            f"Target {target_nm:.2f} nM is too high. For this sample set and "
            f"the '{layout}' layout the maximum achievable pool concentration "
            f"is {max_target:.2f} nM ({limit_desc}).\n"
            f"Fixes: lower the target nM, increase the total volume, or "
            f"concentrate/re-quantify the most dilute library.")

    for s in samples:
        s["sample_ul"] = fmol_per_sample / s["molarity_nm"]

    sum_sample = sum(s["sample_ul"] for s in samples)

    if layout == "normalize":
        well_volume = total_volume_ul / n
        for s in samples:
            s["buffer_ul"] = well_volume - s["sample_ul"]
        buffer_total = sum(s["buffer_ul"] for s in samples)
    else:  # one-tube
        buffer_total = total_volume_ul - sum_sample
        for s in samples:
            s["buffer_ul"] = None

    warnings = []
    for s in samples:
        if round(s["sample_ul"], DECIMALS) < MIN_PIPETTE_UL:
            warnings.append(
                f"Sample '{s['name']}' needs only {s['sample_ul']:.2f} uL, "
                f"below the {MIN_PIPETTE_UL} uL minimum -- it is very "
                f"concentrated. Consider pre-diluting it or increasing the "
                f"total pool volume.")

    summary = {
        "n": n,
        "target_nm": target_nm,
        "total_volume_ul": total_volume_ul,
        "layout": layout,
        "fmol_per_sample": fmol_per_sample,
        "sum_sample_ul": sum_sample,
        "buffer_total_ul": buffer_total,
        "max_target_nm": max_target,
        "well_volume_ul": (total_volume_ul / n) if layout == "normalize" else None,
        "warnings": warnings,
    }
    return samples, summary


# --------------------------------------------------------------------------- #
#  CSV WORKLIST OUTPUT (epMotion format)                                       #
# --------------------------------------------------------------------------- #

_RACK_HEADER = ["Rack", "Src.Barcode", "Src.List Name",
                "Dest.Barcode", "Dest.List Name", "", "", ""]
_TRANSFER_HEADER = ["Barcode ID", "Rack", "Source", "Rack",
                    "Destination", "Volume", "Tool", "Name"]


def _write_worklist(path, transfer_rows):
    """transfer_rows: list of [src_pos, dest_pos, volume, name]."""
    with open(path, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(_RACK_HEADER)
        for r in (1, 2, 3, 4):
            w.writerow([r, "", "", "", "", "", "", ""])
        w.writerow(["", "", "", "", "", "", "", ""])
        w.writerow(_TRANSFER_HEADER)
        for src, dest, vol, name in transfer_rows:
            w.writerow(["", SOURCE_RACK, src, DEST_RACK, dest,
                        _round(vol), TOOL, name])


def write_csvs(samples, summary, out_dir, prefix=""):
    """Write DNA.csv and Buffer.csv. Returns (dna_path, buffer_path)."""
    layout = summary["layout"]
    dna_path = os.path.join(out_dir, f"{prefix}DNA.csv")
    buf_path = os.path.join(out_dir, f"{prefix}Buffer.csv")

    dna_rows, buf_rows = [], []
    if layout == "one-tube":
        for i, s in enumerate(samples):
            dna_rows.append([WELLS[i], POOL_WELL, s["sample_ul"], s["name"]])
        buf_rows.append([BUFFER_SOURCE_POS, POOL_WELL,
                         summary["buffer_total_ul"], "buffer"])
    else:  # normalize
        for i, s in enumerate(samples):
            well = WELLS[i]
            dna_rows.append([well, well, s["sample_ul"], s["name"]])
            buf_rows.append([BUFFER_SOURCE_POS, well, s["buffer_ul"], s["name"]])

    _write_worklist(dna_path, dna_rows)
    _write_worklist(buf_path, buf_rows)
    return dna_path, buf_path


def write_worksheet(samples, summary, path):
    """Human-readable record of the run as a flat CSV."""
    with open(path, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["well", "name", "conc_ng_ul", "size_bp", "molarity_nM",
                    "sample_uL", "buffer_uL"])
        for i, s in enumerate(samples):
            buf = s["buffer_ul"]
            w.writerow([WELLS[i], s["name"], s["conc"], s["size"],
                        round(s["molarity_nm"], 2), _round(s["sample_ul"]),
                        "" if buf is None else _round(buf)])
        w.writerow([])
        w.writerow(["# summary"])
        w.writerow(["layout", summary["layout"]])
        w.writerow(["target_pool_nM", summary["target_nm"]])
        w.writerow(["total_volume_uL", summary["total_volume_ul"]])
        w.writerow(["fmol_per_sample", round(summary["fmol_per_sample"], 2)])
        w.writerow(["total_sample_uL", _round(summary["sum_sample_ul"])])
        w.writerow(["total_buffer_uL", _round(summary["buffer_total_ul"])])


# --------------------------------------------------------------------------- #
#  SAMPLE CSV TEMPLATE + IMPORT                                                #
# --------------------------------------------------------------------------- #

TEMPLATE_HEADER = ["name", "conc_ng_ul", "size_bp"]


def make_template(path):
    with open(path, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(TEMPLATE_HEADER)
        for i in range(1, 4):
            w.writerow([f"sample_{i}", "", ""])


def read_samples_csv(path, allow_blanks=False):
    """
    Read a samples CSV. If allow_blanks is True, missing conc/size are stored as
    None (record-first); otherwise blank values raise PoolingError.
    """
    samples = []
    with open(path, newline="") as fh:
        reader = csv.DictReader(fh)
        cols = {c.strip().lower(): c for c in (reader.fieldnames or [])}
        if "name" not in cols:
            raise PoolingError(
                f"Input CSV needs columns {TEMPLATE_HEADER}; missing 'name'. "
                f"Found: {reader.fieldnames}")
        first_field = (reader.fieldnames or [""])[0]
        for row in reader:
            name = (row.get(cols.get("name", ""), "") or "").strip()
            cval = (row.get(cols.get("conc_ng_ul", ""), "") or "").strip()
            sval = (row.get(cols.get("size_bp", ""), "") or "").strip()
            first = (row.get(first_field, "") or "").strip()
            if name.startswith("#") or first.startswith("#"):
                # A '#'-prefixed row marks the end of the sample table;
                # exported records append a '# parameters'/'# summary' block
                # after it. (DictReader silently drops truly blank rows, so we
                # can't rely on a blank line as the delimiter.) The marker may
                # land in the first column ('well' in worksheets) or in 'name'.
                break
            if not name and not cval and not sval:
                continue
            conc = _parse_optional_float(cval, "conc_ng_ul", name, allow_blanks)
            size = _parse_optional_float(sval, "size_bp", name, allow_blanks)
            samples.append({
                "name": name or f"sample_{len(samples) + 1}",
                "conc": conc, "size": size,
            })
    if not samples:
        raise PoolingError(f"No sample rows found in {path}.")
    return samples


def _parse_optional_float(val, field, name, allow_blanks):
    if val == "":
        if allow_blanks:
            return None
        raise PoolingError(f"Sample '{name}' is missing {field}.")
    try:
        return float(val)
    except ValueError:
        raise PoolingError(f"Sample '{name}' has a non-numeric {field}: {val!r}")


# --------------------------------------------------------------------------- #
#  EXPORT THE FILLED-IN CONTENTS (inputs record) -- CSV or TXT                 #
# --------------------------------------------------------------------------- #

def _param_rows(state):
    return [
        ["platform", state.get("platform") or ""],
        ["preset", state.get("preset") or ""],
        ["target_nm", fmt_num(state.get("target_nm"))],
        ["total_volume_ul", fmt_num(state.get("total_volume_ul"))],
        ["layout", state.get("layout") or ""],
        ["exported_at",
         datetime.datetime.now().isoformat(timespec="seconds")],
    ]


def write_inputs_csv(state, path):
    """
    Dump the current filled-in contents to CSV. The sample table comes first
    with the standard template header, so this file can be re-imported; a
    parameters block follows after a blank line.
    """
    with open(path, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(TEMPLATE_HEADER)
        for s in state.get("samples") or []:
            w.writerow([s.get("name") or "",
                        fmt_num(s.get("conc")), fmt_num(s.get("size"))])
        w.writerow([])
        w.writerow(["# parameters"])
        for row in _param_rows(state):
            w.writerow(row)
    return path


def write_inputs_txt(state, path):
    """Dump the current filled-in contents to a human-readable text file."""
    lines = ["epMotion pooling -- input record",
             f"exported {datetime.datetime.now().isoformat(timespec='seconds')}",
             ""]
    lines.append(f"Platform : {preset_loading_label(state) or '(not set)'}")
    lines.append(f"Target   : {fmt_num(state.get('target_nm')) or '-'} nM")
    lines.append(f"Volume   : {fmt_num(state.get('total_volume_ul')) or '-'} uL")
    lines.append(f"Layout   : {state.get('layout') or '(not set)'}")
    lines.append("")
    lines.append(f"{'Name':<22}{'ng/uL':>10}{'bp':>10}")
    lines.append("-" * 42)
    for s in state.get("samples") or []:
        lines.append(f"{(s.get('name') or '')[:21]:<22}"
                     f"{fmt_num(s.get('conc')) or '-':>10}"
                     f"{fmt_num(s.get('size')) or '-':>10}")
    missing = missing_for_compute(state)
    if missing:
        lines += ["", "Still needed before generating worklists:"]
        lines += [f"  - {m}" for m in missing]
    else:
        lines += ["", "Ready to generate worklists."]
    with open(path, "w") as fh:
        fh.write("\n".join(lines) + "\n")
    return path


def export_inputs(state, path):
    """Write an inputs record, choosing CSV or TXT by the file extension."""
    ext = os.path.splitext(path)[1].lower()
    if ext == ".txt":
        return write_inputs_txt(state, path)
    return write_inputs_csv(state, path)


# --------------------------------------------------------------------------- #
#  PROJECT STATE (record-first: save partial, reopen, finish later)           #
# --------------------------------------------------------------------------- #

PROJECT_VERSION = 1


def new_state():
    return {
        "version": PROJECT_VERSION,
        "platform": None,
        "preset": None,
        "target_nm": None,
        "total_volume_ul": None,
        "layout": None,
        "samples": [],
    }


def save_project(state, path):
    state = dict(state)
    state["version"] = PROJECT_VERSION
    with open(path, "w") as fh:
        json.dump(state, fh, indent=2)
    return path


def load_project(path):
    with open(path) as fh:
        state = json.load(fh)
    base = new_state()
    base.update({k: state.get(k, base[k]) for k in base})
    # normalize samples
    norm = []
    for s in base.get("samples") or []:
        norm.append({
            "name": s.get("name") or f"sample_{len(norm) + 1}",
            "conc": s.get("conc"),
            "size": s.get("size"),
        })
    base["samples"] = norm
    return base
