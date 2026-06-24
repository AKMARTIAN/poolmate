#!/usr/bin/env python3
"""
epMotion equimolar pooling helper -- GUI (Tkinter).

Runs on macOS and Linux with no third-party dependencies (Tkinter ships with
standard Python). Shares the same engine as the terminal app via pooling_core.

Record-first by design: the sample table is front and center, so colleagues can
type names + concentrations during quantification and leave platform / target /
volume / layout blank. Save the run to a .json file and reopen it later to
finish and generate the worklists.

Launch:  python3 pool_gui.py
"""

import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog

import pooling_core as core


class PoolingGUI(ttk.Frame):
    def __init__(self, master):
        super().__init__(master, padding=10)
        self.master = master
        self.project_path = None
        self.grid(sticky="nsew")
        master.columnconfigure(0, weight=1)
        master.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)

        self._build_params()
        self._build_sample_table()
        self._build_actions()
        self._build_output()
        self._on_platform_change()
        self._refresh_status()

    # ---------------- parameters row ---------------- #
    def _build_params(self):
        box = ttk.LabelFrame(self, text="Run parameters (all optional / "
                                        "override any time)", padding=8)
        box.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        for c in range(8):
            box.columnconfigure(c, weight=1)

        ttk.Label(box, text="Platform").grid(row=0, column=0, sticky="w")
        self.platform_var = tk.StringVar(value="")
        plats = [""] + [label for _, label in core.list_platforms()]
        self._label_to_platform = {label: key
                                   for key, label in core.list_platforms()}
        self.platform_cb = ttk.Combobox(box, textvariable=self.platform_var,
                                        values=plats, state="readonly", width=16)
        self.platform_cb.grid(row=1, column=0, sticky="ew", padx=(0, 6))
        self.platform_cb.bind("<<ComboboxSelected>>", self._on_platform_change)

        ttk.Label(box, text="Loading preset").grid(row=0, column=1, sticky="w")
        self.preset_var = tk.StringVar(value="")
        self.preset_cb = ttk.Combobox(box, textvariable=self.preset_var,
                                      values=[], state="readonly", width=18)
        self.preset_cb.grid(row=1, column=1, sticky="ew", padx=(0, 6))
        self.preset_cb.bind("<<ComboboxSelected>>", self._on_preset_change)

        ttk.Label(box, text="Target nM").grid(row=0, column=2, sticky="w")
        self.target_var = tk.StringVar()
        ttk.Entry(box, textvariable=self.target_var, width=8).grid(
            row=1, column=2, sticky="ew", padx=(0, 6))

        ttk.Label(box, text="Volume uL").grid(row=0, column=3, sticky="w")
        self.volume_var = tk.StringVar()
        ttk.Entry(box, textvariable=self.volume_var, width=8).grid(
            row=1, column=3, sticky="ew", padx=(0, 6))

        ttk.Label(box, text="Layout").grid(row=0, column=4, sticky="w")
        self.layout_var = tk.StringVar(value="")
        ttk.Combobox(box, textvariable=self.layout_var,
                     values=["", "one-tube", "normalize"], state="readonly",
                     width=12).grid(row=1, column=4, sticky="ew")

        self.preset_note = ttk.Label(box, text="", wraplength=720,
                                     foreground="#555")
        self.preset_note.grid(row=2, column=0, columnspan=8, sticky="w",
                              pady=(6, 0))

    # ---------------- sample table ---------------- #
    def _build_sample_table(self):
        box = ttk.LabelFrame(self, text="Samples (record names + "
                                        "concentrations first; size optional)",
                             padding=8)
        box.grid(row=2, column=0, sticky="nsew")
        box.columnconfigure(0, weight=1)
        box.rowconfigure(0, weight=1)

        cols = ("name", "conc", "size")
        self.tree = ttk.Treeview(box, columns=cols, show="headings",
                                 height=10, selectmode="browse")
        self.tree.heading("name", text="Name / number")
        self.tree.heading("conc", text="Conc (ng/uL)")
        self.tree.heading("size", text="Size (bp)")
        self.tree.column("name", width=200)
        self.tree.column("conc", width=120, anchor="e")
        self.tree.column("size", width=120, anchor="e")
        self.tree.grid(row=0, column=0, sticky="nsew")
        sb = ttk.Scrollbar(box, orient="vertical", command=self.tree.yview)
        sb.grid(row=0, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.bind("<Double-1>", self._edit_cell)

        # entry row for quick add
        addrow = ttk.Frame(box)
        addrow.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(8, 0))
        self.in_name = tk.StringVar()
        self.in_conc = tk.StringVar()
        self.in_size = tk.StringVar()
        ttk.Label(addrow, text="Name").grid(row=0, column=0)
        e_name = ttk.Entry(addrow, textvariable=self.in_name, width=18)
        e_name.grid(row=0, column=1, padx=4)
        ttk.Label(addrow, text="ng/uL").grid(row=0, column=2)
        ttk.Entry(addrow, textvariable=self.in_conc, width=10).grid(
            row=0, column=3, padx=4)
        ttk.Label(addrow, text="bp").grid(row=0, column=4)
        e_size = ttk.Entry(addrow, textvariable=self.in_size, width=10)
        e_size.grid(row=0, column=5, padx=4)
        ttk.Button(addrow, text="Add sample", command=self._add_sample).grid(
            row=0, column=6, padx=4)
        ttk.Button(addrow, text="Remove selected",
                   command=self._remove_sample).grid(row=0, column=7, padx=4)
        e_size.bind("<Return>", lambda e: self._add_sample())
        e_name.bind("<Return>", lambda e: self.in_conc and None)

    # ---------------- action buttons ---------------- #
    def _build_actions(self):
        bar = ttk.Frame(self)
        bar.grid(row=3, column=0, sticky="ew", pady=8)
        ttk.Button(bar, text="Import CSV...",
                   command=self._import_csv).pack(side="left")
        ttk.Button(bar, text="Save run...",
                   command=self._save).pack(side="left", padx=4)
        ttk.Button(bar, text="Open run...",
                   command=self._open).pack(side="left")
        ttk.Button(bar, text="Blank CSV template...",
                   command=self._make_template).pack(side="left", padx=4)
        ttk.Button(bar, text="Export contents...",
                   command=self._export_contents).pack(side="left")
        ttk.Button(bar, text="Generate worklists",
                   command=self._generate).pack(side="right")
        self.status = ttk.Label(bar, text="", foreground="#0a0")
        self.status.pack(side="right", padx=10)

    # ---------------- output console ---------------- #
    def _build_output(self):
        box = ttk.LabelFrame(self, text="Results", padding=6)
        box.grid(row=4, column=0, sticky="nsew")
        box.columnconfigure(0, weight=1)
        self.out = tk.Text(box, height=12, wrap="none",
                           font=("Menlo", 11) if _has_menlo() else None)
        self.out.grid(row=0, column=0, sticky="nsew")
        sb = ttk.Scrollbar(box, orient="vertical", command=self.out.yview)
        sb.grid(row=0, column=1, sticky="ns")
        self.out.configure(yscrollcommand=sb.set, state="disabled")

    # ---------------- behavior ---------------- #
    def _on_platform_change(self, *_):
        label = self.platform_var.get()
        platform = self._label_to_platform.get(label)
        if not platform:
            self.preset_cb.configure(values=[])
            self.preset_var.set("")
            self.preset_note.configure(text="")
            return
        loadings = [l for _, l in core.list_presets(platform)]
        self._loading_to_key = {l: k
                                for k, l in core.list_presets(platform)}
        self.preset_cb.configure(values=loadings)
        # default preset
        default_key = core.PRESETS[platform]["default"]
        default_loading = core.PRESETS[platform]["options"][default_key]["loading"]
        self.preset_var.set(default_loading)
        self._on_preset_change()

    def _on_preset_change(self, *_):
        label = self.platform_var.get()
        platform = self._label_to_platform.get(label)
        if not platform:
            return
        key = self._loading_to_key.get(self.preset_var.get())
        if not key:
            return
        opt = core.PRESETS[platform]["options"][key]
        self.target_var.set(str(opt["target_nm"]))
        self.volume_var.set(str(opt["volume_ul"]))
        self.preset_note.configure(text=opt["note"])
        self._refresh_status()

    def _add_sample(self):
        name = self.in_name.get().strip()
        if not name:
            messagebox.showinfo("Add sample", "Enter a sample name.")
            return
        self.tree.insert("", "end",
                         values=(name, self.in_conc.get().strip(),
                                 self.in_size.get().strip()))
        self.in_name.set("")
        self.in_conc.set("")
        # keep size (often shared)
        self._refresh_status()

    def _remove_sample(self):
        for item in self.tree.selection():
            self.tree.delete(item)
        self._refresh_status()

    def _edit_cell(self, event):
        item = self.tree.identify_row(event.y)
        col = self.tree.identify_column(event.x)
        if not item or not col:
            return
        cidx = int(col[1:]) - 1
        x, y, w, h = self.tree.bbox(item, col)
        val = self.tree.set(item, self.tree["columns"][cidx])
        ent = ttk.Entry(self.tree)
        ent.place(x=x, y=y, width=w, height=h)
        ent.insert(0, val)
        ent.focus()

        def commit(_=None):
            self.tree.set(item, self.tree["columns"][cidx], ent.get().strip())
            ent.destroy()
            self._refresh_status()
        ent.bind("<Return>", commit)
        ent.bind("<FocusOut>", commit)
        ent.bind("<Escape>", lambda e: ent.destroy())

    # ---------------- state <-> widgets ---------------- #
    def _collect_state(self):
        state = core.new_state()
        label = self.platform_var.get()
        state["platform"] = self._label_to_platform.get(label)
        if state["platform"]:
            state["preset"] = getattr(self, "_loading_to_key", {}).get(
                self.preset_var.get())
        state["target_nm"] = _parse_float(self.target_var.get())
        state["total_volume_ul"] = _parse_float(self.volume_var.get())
        state["layout"] = self.layout_var.get() or None
        samples = []
        for item in self.tree.get_children():
            name, conc, size = self.tree.item(item, "values")
            samples.append({
                "name": name,
                "conc": _parse_float(conc),
                "size": _parse_float(size),
            })
        state["samples"] = samples
        return state

    def _load_state(self, state):
        # platform
        plabel = ""
        if state.get("platform") in core.PRESETS:
            plabel = core.PRESETS[state["platform"]]["label"]
        self.platform_var.set(plabel)
        self._on_platform_change()
        if state.get("platform") in core.PRESETS and state.get("preset"):
            opt = core.PRESETS[state["platform"]]["options"].get(state["preset"])
            if opt:
                self.preset_var.set(opt["loading"])
                self._on_preset_change()
        self.target_var.set(_fmt(state.get("target_nm")))
        self.volume_var.set(_fmt(state.get("total_volume_ul")))
        self.layout_var.set(state.get("layout") or "")
        for item in self.tree.get_children():
            self.tree.delete(item)
        for s in state.get("samples") or []:
            self.tree.insert("", "end", values=(
                s.get("name") or "", _fmt(s.get("conc")), _fmt(s.get("size"))))
        self._refresh_status()

    def _refresh_status(self):
        state = self._collect_state()
        missing = core.missing_for_compute(state)
        if missing:
            self.status.configure(
                text=f"{len(missing)} item(s) to fill", foreground="#b80")
        else:
            self.status.configure(text="Ready to generate", foreground="#0a0")

    # ---------------- file ops ---------------- #
    def _import_csv(self):
        path = filedialog.askopenfilename(
            title="Import samples CSV",
            filetypes=[("CSV", "*.csv"), ("All", "*.*")])
        if not path:
            return
        try:
            samples = core.read_samples_csv(path, allow_blanks=True)
        except core.PoolingError as e:
            messagebox.showerror("Import failed", str(e))
            return
        for s in samples:
            self.tree.insert("", "end", values=(
                s["name"], _fmt(s.get("conc")), _fmt(s.get("size"))))
        self._refresh_status()

    def _make_template(self):
        path = filedialog.asksaveasfilename(
            title="Save blank sample template", defaultextension=".csv",
            initialfile="samples.csv", filetypes=[("CSV", "*.csv")])
        if not path:
            return
        core.make_template(path)
        messagebox.showinfo("Template", f"Wrote blank template to:\n{path}")

    def _save(self):
        path = filedialog.asksaveasfilename(
            title="Save run", defaultextension=".json",
            initialfile=self.project_path or "pooling_run.json",
            filetypes=[("JSON run", "*.json")])
        if not path:
            return
        core.save_project(self._collect_state(), path)
        self.project_path = path
        self.status.configure(text=f"Saved {os.path.basename(path)}",
                              foreground="#0a0")

    def _open(self):
        path = filedialog.askopenfilename(
            title="Open run", filetypes=[("JSON run", "*.json"), ("All", "*.*")])
        if not path:
            return
        try:
            state = core.load_project(path)
        except Exception as e:  # noqa: BLE001
            messagebox.showerror("Open failed", str(e))
            return
        self.project_path = path
        self._load_state(state)

    # ---------------- export current contents ---------------- #
    def _export_contents(self):
        state = self._collect_state()
        if not state.get("samples"):
            messagebox.showinfo("Export", "Add at least one sample first.")
            return
        path = filedialog.asksaveasfilename(
            title="Export filled-in contents",
            defaultextension=".csv",
            initialfile=core.auto_dirname(state, base_prefix="inputs") + ".csv",
            filetypes=[("CSV (re-importable)", "*.csv"),
                       ("Text file", "*.txt")])
        if not path:
            return
        core.export_inputs(state, path)
        self.status.configure(text=f"Exported {os.path.basename(path)}",
                              foreground="#0a0")
        messagebox.showinfo("Export", f"Wrote:\n{path}")

    # ---------------- compute ---------------- #
    def _generate(self):
        state = self._collect_state()
        missing = core.missing_for_compute(state)
        if missing:
            messagebox.showwarning(
                "Not ready",
                "Still needed before generating:\n  - " + "\n  - ".join(missing))
            return
        try:
            samples, summary = core.compute_pool(
                [dict(s) for s in state["samples"]],
                state["target_nm"], state["total_volume_ul"], state["layout"])
        except core.PoolingError as e:
            messagebox.showerror("Cannot pool", str(e))
            return

        base = filedialog.askdirectory(
            title="Choose a PARENT folder (a unique subfolder is created in it)")
        if not base:
            return
        # Auto, hard-to-collide folder name; user may edit it.
        auto = core.auto_dirname(state)
        name = simpledialog.askstring(
            "Output folder name",
            "A new subfolder will be created here.\nName (edit if you like):",
            initialvalue=auto, parent=self)
        if not name:
            return
        out_dir = os.path.join(base, name)
        os.makedirs(out_dir, exist_ok=True)
        dna, buf = core.write_csvs(samples, summary, out_dir)
        ws = os.path.join(out_dir, "pooling_worksheet.csv")
        core.write_worksheet(samples, summary, ws)
        rec = os.path.join(out_dir, "inputs.csv")
        core.write_inputs_csv(state, rec)
        self._show_results(samples, summary, [dna, buf, ws, rec])

    def _show_results(self, samples, summary, paths):
        lines = []
        lines.append(f"Equal moles: {summary['fmol_per_sample']:.2f} fmol per sample")
        lines.append(f"{'Well':<5}{'Name':<16}{'ng/uL':>8}{'bp':>7}"
                     f"{'nM':>9}{'Sample uL':>11}{'Buffer uL':>11}")
        lines.append("-" * 67)
        for i, s in enumerate(samples):
            buf = s["buffer_ul"]
            buf_str = "(pooled)" if buf is None else f"{core._round(buf):.1f}"
            lines.append(f"{core.WELLS[i]:<5}{s['name'][:15]:<16}"
                         f"{s['conc']:>8.2f}{int(s['size']):>7}"
                         f"{s['molarity_nm']:>9.2f}"
                         f"{core._round(s['sample_ul']):>11.1f}{buf_str:>11}")
        lines.append("-" * 67)
        lines.append(f"Total sample volume: {core._round(summary['sum_sample_ul'])} uL")
        if summary["layout"] == "one-tube":
            lines.append(f"Buffer into {core.POOL_WELL}: "
                         f"{core._round(summary['buffer_total_ul'])} uL")
        else:
            lines.append(f"Buffer total: {core._round(summary['buffer_total_ul'])} uL "
                         f"(each well -> {core._round(summary['well_volume_ul'])} uL)")
        for w in summary["warnings"]:
            lines.append(f"[!] {w}")
        lines.append("")
        lines.append("Wrote:")
        for pth in paths:
            lines.append(f"  {pth}")
        lines.append("\nLoad DNA.csv then Buffer.csv into the epMotion run.")

        self.out.configure(state="normal")
        self.out.delete("1.0", "end")
        self.out.insert("1.0", "\n".join(lines))
        self.out.configure(state="disabled")
        self.status.configure(text="Worklists written", foreground="#0a0")


def _parse_float(v):
    if v in (None, ""):
        return None
    try:
        return float(v)
    except (ValueError, TypeError):
        return None


def _fmt(v):
    if v in (None, ""):
        return ""
    if isinstance(v, float) and v.is_integer():
        return str(int(v))
    return str(v)


def _has_menlo():
    try:
        import tkinter.font as tkfont
        return "Menlo" in tkfont.families()
    except Exception:  # noqa: BLE001
        return False


def main():
    root = tk.Tk()
    root.title("epMotion equimolar pooling helper")
    root.geometry("900x720")
    try:
        ttk.Style().theme_use("clam")
    except tk.TclError:
        pass
    PoolingGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
