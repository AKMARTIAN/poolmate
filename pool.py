#!/usr/bin/env python3
"""
epMotion equimolar pooling helper -- terminal app.

Two ways to use it:

  * Menu mode (just run `python3 pool.py`): a record-first workflow. You can
    type in sample names and concentrations FIRST and leave platform / target /
    volume / layout for later -- save the run to a .json file and reopen it to
    finish. Nothing is required up front except sample names.

  * One-shot CLI mode: provide everything on the command line, e.g.
        python3 pool.py --input samples.csv --platform illumina \
            --target-nm 4 --volume 50 --layout one-tube
    or load a saved run:
        python3 pool.py --project myrun.json

Helpers:
    python3 pool.py --make-template samples.csv   # blank sample CSV

Pure Python 3 standard library -- runs as-is on macOS and Linux. A GUI version
(pool_gui.py) shares the same engine (pooling_core.py).
"""

import argparse
import os
import sys

import pooling_core as core


# --------------------------------------------------------------------------- #
#  Small input helpers                                                         #
# --------------------------------------------------------------------------- #

def _ask(prompt, cast=str, default=None, allow_blank=False, validate=None):
    """Prompt until valid. allow_blank returns None on empty input."""
    while True:
        suffix = f" [{default}]" if default not in (None, "") else ""
        raw = input(f"{prompt}{suffix}: ").strip()
        if not raw:
            if default not in (None, ""):
                return default
            if allow_blank:
                return None
            print("  Please enter a value.")
            continue
        try:
            val = cast(raw)
        except ValueError:
            print("  Invalid value, try again.")
            continue
        if validate and not validate(val):
            print("  Out of range, try again.")
            continue
        return val


# --------------------------------------------------------------------------- #
#  State display                                                               #
# --------------------------------------------------------------------------- #

def print_state(state):
    print("\n  Current run")
    print("  -----------")
    plat = state.get("platform")
    plabel = core.PRESETS[plat]["label"] if plat in core.PRESETS else "(not set)"
    preset = state.get("preset")
    ploading = ""
    if plat in core.PRESETS and preset in core.PRESETS[plat]["options"]:
        ploading = " / " + core.PRESETS[plat]["options"][preset]["loading"]
    print(f"  Platform : {plabel}{ploading}")
    print(f"  Target   : {_fmt(state.get('target_nm'))} nM")
    print(f"  Volume   : {_fmt(state.get('total_volume_ul'))} uL")
    print(f"  Layout   : {state.get('layout') or '(not set)'}")
    samples = state.get("samples") or []
    print(f"  Samples  : {len(samples)}")
    if samples:
        print(f"    {'#':<3}{'Name':<18}{'ng/uL':>8}{'bp':>8}")
        for i, s in enumerate(samples, 1):
            print(f"    {i:<3}{(s['name'] or '')[:17]:<18}"
                  f"{_fmt(s.get('conc')):>8}{_fmt(s.get('size')):>8}")
    missing = core.missing_for_compute(state)
    if missing:
        print(f"\n  Still needed before generating worklists:")
        for m in missing:
            print(f"    - {m}")
    else:
        print("\n  Ready to generate worklists.")
    print()


def _fmt(v):
    if v in (None, ""):
        return "-"
    if isinstance(v, float) and v.is_integer():
        return str(int(v))
    return str(v)


# --------------------------------------------------------------------------- #
#  Editors                                                                     #
# --------------------------------------------------------------------------- #

def edit_samples(state):
    """Add samples (record-first: size can be left blank for now)."""
    print("\nAdd samples. Concentration and size can be left blank now and "
          "filled in later. Blank name to stop.")
    same = input("Do all samples share one fragment size? Enter it now (bp) "
                 "or leave blank: ").strip()
    shared = float(same) if same else None
    while True:
        idx = len(state["samples"]) + 1
        name = input(f"  Sample {idx} name/number (blank to stop): ").strip()
        if not name:
            break
        conc = _ask(f"    {name} concentration (ng/uL, blank=later)",
                    cast=float, allow_blank=True, validate=lambda v: v > 0)
        if shared is not None:
            size = shared
        else:
            size = _ask(f"    {name} fragment size (bp, blank=later)",
                        cast=float, allow_blank=True, validate=lambda v: v > 0)
        state["samples"].append({"name": name, "conc": conc, "size": size})
    print(f"  {len(state['samples'])} sample(s) recorded.")


def fill_missing_sample_values(state):
    """Walk samples that still miss conc/size and fill them in."""
    todo = [s for s in state["samples"]
            if s.get("conc") in (None, "") or s.get("size") in (None, "")]
    if not todo:
        print("  All samples already have concentration and size.")
        return
    for s in todo:
        print(f"  {s['name']}:")
        if s.get("conc") in (None, ""):
            s["conc"] = _ask("    concentration (ng/uL, blank=skip)",
                             cast=float, allow_blank=True,
                             validate=lambda v: v > 0)
        if s.get("size") in (None, ""):
            s["size"] = _ask("    fragment size (bp, blank=skip)",
                             cast=float, allow_blank=True,
                             validate=lambda v: v > 0)


def set_platform(state):
    plats = core.list_platforms()
    print("\nPlatform:")
    for i, (key, label) in enumerate(plats, 1):
        print(f"  {i}) {label}")
    c = _ask("Select", cast=int, validate=lambda v: 1 <= v <= len(plats))
    platform = plats[c - 1][0]
    state["platform"] = platform

    presets = core.list_presets(platform)
    print(f"\nLoading preset for {core.PRESETS[platform]['label']}:")
    for i, (key, loading) in enumerate(presets, 1):
        note = core.PRESETS[platform]["options"][key]["note"]
        print(f"  {i}) {loading}")
        print(f"       {note}")
    pc = _ask("Select", cast=int, default=1,
              validate=lambda v: 1 <= v <= len(presets))
    pkey = presets[pc - 1][0]
    state["preset"] = pkey
    opt = core.PRESETS[platform]["options"][pkey]
    # Apply the preset's target/volume as defaults (user can still override).
    state["target_nm"] = opt["target_nm"]
    state["total_volume_ul"] = opt["volume_ul"]
    print(f"  Applied {opt['loading']} -> target {opt['target_nm']} nM, "
          f"volume {opt['volume_ul']} uL (override these any time).")


def set_target(state):
    state["target_nm"] = _ask("Target pool concentration (nM)", cast=float,
                              default=state.get("target_nm"),
                              validate=lambda v: v > 0)


def set_volume(state):
    state["total_volume_ul"] = _ask("Total pool volume (uL)", cast=float,
                                    default=state.get("total_volume_ul"),
                                    validate=lambda v: v > 0)


def set_layout(state):
    print("\nLayout:")
    print("  1) one-tube  -> all samples combined into one well")
    print("  2) normalize -> each sample diluted in its own well")
    c = _ask("Select", cast=int, default=1, validate=lambda v: v in (1, 2))
    state["layout"] = "one-tube" if c == 1 else "normalize"


# --------------------------------------------------------------------------- #
#  Output                                                                      #
# --------------------------------------------------------------------------- #

def print_results(samples, summary):
    layout = summary["layout"]
    print(f"\n  Equal moles: {summary['fmol_per_sample']:.2f} fmol per sample")
    header = (f"  {'Well':<5}{'Name':<16}{'ng/uL':>8}{'bp':>7}"
              f"{'nM':>9}{'Sample uL':>11}{'Buffer uL':>11}")
    print(header)
    print("  " + "-" * (len(header) - 2))
    for i, s in enumerate(samples):
        buf = s["buffer_ul"]
        buf_str = "(pooled)" if buf is None else f"{core._round(buf):.1f}"
        print(f"  {core.WELLS[i]:<5}{s['name'][:15]:<16}{s['conc']:>8.2f}"
              f"{int(s['size']):>7}{s['molarity_nm']:>9.2f}"
              f"{core._round(s['sample_ul']):>11.1f}{buf_str:>11}")
    print("  " + "-" * (len(header) - 2))
    print(f"  Total sample volume : {core._round(summary['sum_sample_ul']):.1f} uL")
    if layout == "one-tube":
        print(f"  Buffer into {core.POOL_WELL}     : "
              f"{core._round(summary['buffer_total_ul']):.1f} uL")
    else:
        print(f"  Buffer total        : "
              f"{core._round(summary['buffer_total_ul']):.1f} uL "
              f"(each well -> {core._round(summary['well_volume_ul'])} uL)")
    for w in summary["warnings"]:
        print(f"  [!] {w}")
    print()


def generate(state, base_dir=".", folder=None, prefix=""):
    missing = core.missing_for_compute(state)
    if missing:
        print("\n  Cannot generate yet -- still needed:")
        for m in missing:
            print(f"    - {m}")
        return False
    try:
        samples, summary = core.compute_pool(
            [dict(s) for s in state["samples"]],
            state["target_nm"], state["total_volume_ul"], state["layout"])
    except core.PoolingError as e:
        print(f"\nERROR: {e}\n", file=sys.stderr)
        return False
    print_results(samples, summary)
    # Each run lands in its own uniquely named folder so nothing is overwritten.
    folder = folder or core.auto_dirname(state)
    out_dir = os.path.join(base_dir, folder)
    os.makedirs(out_dir, exist_ok=True)
    dna, buf = core.write_csvs(samples, summary, out_dir, prefix)
    ws = os.path.join(out_dir, f"{prefix}pooling_worksheet.csv")
    core.write_worksheet(samples, summary, ws)
    # Also drop the inputs record alongside the worklists.
    rec = os.path.join(out_dir, f"{prefix}inputs.csv")
    core.write_inputs_csv(state, rec)
    print(f"  Output folder: {out_dir}")
    print(f"  Wrote:\n    {dna}\n    {buf}\n    {ws}\n    {rec}")
    print("\n  Load DNA.csv then Buffer.csv into the epMotion run.\n")
    return True


def export_inputs(state):
    """Menu action: write the current contents to a CSV or text file."""
    print("\n  Export current contents:")
    print("    1) CSV (re-importable sample table + parameters)")
    print("    2) Text file (human-readable)")
    c = input("  Choose [1]: ").strip() or "1"
    ext = ".txt" if c == "2" else ".csv"
    default = core.auto_dirname(state, base_prefix="inputs") + ext
    path = input(f"  Save as [{default}]: ").strip() or default
    if not os.path.splitext(path)[1]:
        path += ext
    core.export_inputs(state, path)
    print(f"  Wrote {path}")


# --------------------------------------------------------------------------- #
#  Menu loop                                                                   #
# --------------------------------------------------------------------------- #

def menu(state, project_path=None):
    while True:
        print_state(state)
        print("  1) Add samples              6) Save run (.json)")
        print("  2) Fill in sample conc/size 7) Export contents (csv/txt)")
        print("  3) Set platform & preset    8) Generate worklists")
        print("  4) Set target nM / volume   9) Quit")
        print("  5) Set layout")
        choice = input("  Choose: ").strip()
        if choice == "1":
            edit_samples(state)
        elif choice == "2":
            fill_missing_sample_values(state)
        elif choice == "3":
            set_platform(state)
        elif choice == "4":
            set_target(state)
            set_volume(state)
        elif choice == "5":
            set_layout(state)
        elif choice == "6":
            default = project_path or "pooling_run.json"
            path = input(f"  Save to [{default}]: ").strip() or default
            core.save_project(state, path)
            project_path = path
            print(f"  Saved to {path}")
        elif choice == "7":
            export_inputs(state)
        elif choice == "8":
            base = input("  Base folder [.]: ").strip() or "."
            auto = core.auto_dirname(state)
            name = input(f"  Output subfolder [{auto}]: ").strip() or auto
            generate(state, base_dir=base, folder=name)
        elif choice in ("9", "q", "quit", "exit"):
            # Offer to save unsaved work
            if core.missing_for_compute(state) or True:
                yn = input("  Save before quitting? (y/N): ").strip().lower()
                if yn == "y":
                    default = project_path or "pooling_run.json"
                    path = input(f"  Save to [{default}]: ").strip() or default
                    core.save_project(state, path)
                    print(f"  Saved to {path}")
            print("  Bye.")
            return
        else:
            print("  Unknown choice.")


def start_menu():
    print("=" * 60)
    print(" epMotion equimolar pooling helper")
    print("=" * 60)
    print("\n  1) New run (record samples now, finish later)")
    print("  2) Open a saved run (.json)")
    print("  3) Import samples from a CSV")
    choice = input("  Choose [1]: ").strip() or "1"
    if choice == "2":
        path = input("  Path to .json run: ").strip()
        state = core.load_project(path)
        return state, path
    elif choice == "3":
        path = input("  Path to samples CSV: ").strip()
        state = core.new_state()
        state["samples"] = core.read_samples_csv(path, allow_blanks=True)
        return state, None
    else:
        state = core.new_state()
        # Jump straight to recording samples -- the record-first flow.
        edit_samples(state)
        return state, None


# --------------------------------------------------------------------------- #
#  CLI                                                                         #
# --------------------------------------------------------------------------- #

def main(argv=None):
    p = argparse.ArgumentParser(
        description="Equimolar library pooling -> epMotion worklist CSVs.")
    p.add_argument("--input", help="CSV with columns name,conc_ng_ul,size_bp")
    p.add_argument("--project", help="Load a saved .json run")
    p.add_argument("--make-template", metavar="PATH",
                   help="Write a blank sample CSV template and exit")
    p.add_argument("--platform", choices=list(core.PRESETS))
    p.add_argument("--preset", help="Loading preset key for the platform")
    p.add_argument("--target-nm", type=float)
    p.add_argument("--volume", type=float)
    p.add_argument("--layout", choices=["one-tube", "normalize"])
    p.add_argument("--base-dir", default=".",
                   help="Parent folder; a unique subfolder is auto-created in it")
    p.add_argument("--out-dir", default=None,
                   help="Explicit output folder name (overrides the auto name)")
    p.add_argument("--prefix", default="")
    p.add_argument("--save", metavar="PATH",
                   help="Save the (possibly partial) run to JSON and exit")
    p.add_argument("--export", metavar="PATH",
                   help="Export the filled-in contents to .csv or .txt and exit")
    args = p.parse_args(argv)

    if args.make_template:
        core.make_template(args.make_template)
        print(f"Wrote blank sample template to {args.make_template}")
        return 0

    try:
        # Decide: interactive menu, or one-shot from flags.
        one_shot = args.input or args.project
        if not one_shot:
            state, path = start_menu()
            menu(state, path)
            return 0

        # Build state from project and/or input + flags.
        if args.project:
            state = core.load_project(args.project)
        else:
            state = core.new_state()
        if args.input:
            state["samples"] = core.read_samples_csv(args.input, allow_blanks=True)

        # Apply platform preset defaults first, then explicit overrides.
        if args.platform:
            state["platform"] = args.platform
            opt = core.resolve_preset(args.platform, args.preset)
            if opt:
                state["preset"] = args.preset or core.PRESETS[args.platform]["default"]
                state.setdefault("target_nm", None)
                if state["target_nm"] in (None, ""):
                    state["target_nm"] = opt["target_nm"]
                if state["total_volume_ul"] in (None, ""):
                    state["total_volume_ul"] = opt["volume_ul"]
        if args.target_nm is not None:
            state["target_nm"] = args.target_nm
        if args.volume is not None:
            state["total_volume_ul"] = args.volume
        if args.layout:
            state["layout"] = args.layout

        if args.save:
            core.save_project(state, args.save)
            print(f"Saved run to {args.save}")
            missing = core.missing_for_compute(state)
            if missing:
                print("Still needed before generating worklists:")
                for m in missing:
                    print(f"  - {m}")
            return 0

        if args.export:
            core.export_inputs(state, args.export)
            print(f"Exported contents to {args.export}")
            return 0

        ok = generate(state, base_dir=args.base_dir, folder=args.out_dir,
                      prefix=args.prefix)
        return 0 if ok else 1

    except core.PoolingError as e:
        print(f"\nERROR: {e}\n", file=sys.stderr)
        return 1
    except (KeyboardInterrupt, EOFError):
        print("\nCancelled.")
        return 130


if __name__ == "__main__":
    sys.exit(main())
